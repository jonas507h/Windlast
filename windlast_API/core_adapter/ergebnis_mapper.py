# api_mapper.py
from typing import Dict, Any, Mapping, Iterable
from math import isfinite, isinf, isnan
from dataclasses import is_dataclass, asdict
from windlast_CORE.datenstruktur.enums import Norm, Nachweis

# ---------- API keys (same as before) ----------
_NORM_KEY = {
    Norm.DIN_EN_13814_2005_06:    "EN_13814_2005",
    Norm.DIN_EN_17879_2024_08:    "EN_17879_2024",
    Norm.DIN_EN_1991_1_4_2010_12: "EN_1991_1_4_2010",
}

# ---------- helpers ----------
def _enum_to_str(x):
    return getattr(x, "name", str(x))

def _to_primitive(obj):
    """
    Safe serializer for enums/dataclasses/mappings/lists (used for CONTEXT only).
    We do NOT touch numbers here (numbers go through _jsonify_number elsewhere),
    this is just to turn arbitrary context into JSON-safe primitives.
    """
    if obj is None:
        return None
    # --- Zahlen: hier ebenfalls absichern ---
    if isinstance(obj, float):
        return _jsonify_number(obj)
    if isinstance(obj, int):
        return obj
    # enums
    if hasattr(obj, "__class__") and hasattr(obj.__class__, "__members__"):
        return _enum_to_str(obj)
    # dataclass
    if is_dataclass(obj):
        return {k: _to_primitive(v) for k, v in asdict(obj).items()}
    # mapping
    if isinstance(obj, Mapping):
        out = {}
        for k, v in obj.items():
            kk = _enum_to_str(k) if not isinstance(k, str) else k
            out[kk] = _to_primitive(v)
        return out
    # iterable
    if isinstance(obj, (list, tuple, set)):
        return [_to_primitive(v) for v in obj]
    # primitives
    return obj

def _jsonify_number(x):
    """float -> JSON-safe (NaN -> None, keep +/-INF as strings)."""
    try:
        v = float(x)
    except Exception:
        return None
    if isnan(v):
        return None
    if isinf(v):
        return "INF" if v > 0 else "-INF"
    return v

def _collect_messages_from_list(items: Iterable[Any], fallback_szenario: str | None = None):
    """
    Normalize a list of message-like objects to:
      { "severity": "warn|error|hint|info", "text": "...", "context": { ... } }
    Expected attributes (best effort): .severity, .text (or .message), .code (optional), .context (mapping-like).
    """
    out = []
    if not items:
        return out

    for m in items:
        # try attribute access, then dict-style
        severity = getattr(m, "severity", None) or (isinstance(m, Mapping) and m.get("severity"))
        text     = getattr(m, "text", None)     or (isinstance(m, Mapping) and (m.get("text") or m.get("message")))
        code     = getattr(m, "code", None)     or (isinstance(m, Mapping) and m.get("code"))
        context  = getattr(m, "context", None)  or (isinstance(m, Mapping) and m.get("context")) or {}

        # normalize context (make it JSON-safe, normalize enums to names)
        ctx = _to_primitive(context) or {}
        # ensure there is a scenario key if we got a fallback (useful for messages without explicit scenario)
        if fallback_szenario and "szenario" not in ctx and "scenario" not in ctx:
            ctx["szenario"] = fallback_szenario

        # normalize severity to lower string if present
        if isinstance(severity, str):
            sev = severity.lower()
        else:
            sev = _enum_to_str(severity).lower() if severity is not None else None

        if text is None and code is not None:
            text = str(code)

        out.append({
            "severity": sev,
            "text": None if text is None else str(text),
            "code": None if code is None else str(code),
            "context": ctx
        })
    return out

# ----- docs: (bundle, ctx) -> JSON -----

_ROLE_ORDER = {"relevant": 3, "entscheidungsrelevant": 2, "irrelevant": 1, None: 0}

def _normalize_doc_bundle(bundle, ctx):
    """
    bundle: Mapping[str, Any] (siehe make_docbundle), ctx: dict
    -> JSON-sicheres Dict
    """
    b = dict(bundle or {})
    out = {
        "title": b.get("titel") or b.get("title"),
        "value": _to_primitive(b.get("wert")),
        "unit": b.get("einheit") or b.get("unit"),
        "formula": b.get("formel"),
        "formula_source": b.get("quelle_formel"),
        "symbols": _to_primitive(b.get("formelzeichen")),
        "symbols_source": _to_primitive(b.get("quelle_formelzeichen")),
        "items": _to_primitive(b.get("einzelwerte")),
        "items_source": _to_primitive(b.get("quelle_einzelwerte")),
        "context": _to_primitive(ctx or {}),
    }
    return out

def _collect_docs_from_list(items):
    """
    items: List[Tuple[bundle, ctx]]
    - normalisiert Bundles
    - dedupliziert *nur* echte Duplikate über einen erweiterten Schlüssel:
      (title, doc_type, nachweis, szenario, windrichtung_deg, achse_index, element_id, segment_index, ref_nachweis)
      → Falls identisch, gewinnt die höhere Rolle (relevant > entscheidungsrelevant > irrelevant).
    """
    if not items:
        return []

    dedup = {}  # key -> doc
    for bundle, ctx in items:
        doc = _normalize_doc_bundle(bundle, ctx)
        c = doc["context"] or {}
        key = (
            doc["title"],
            c.get("doc_type"),
            c.get("nachweis"),                         # wichtig: pro Nachweis getrennt
            c.get("szenario") or c.get("scenario"),
            c.get("windrichtung_deg"),
            c.get("achse_index"),
            c.get("element_id") or c.get("element_id_intern"),
            c.get("segment_index"),
            c.get("ref_nachweis"),                     # z.B. LOADS, falls gesetzt
        )
        role_new = (c.get("rolle") or c.get("role"))

        if key in dedup:
            role_old = (dedup[key]["context"] or {}).get("rolle")
            if _ROLE_ORDER.get(role_new, 0) > _ROLE_ORDER.get(role_old, 0):
                dedup[key] = doc
        else:
            dedup[key] = doc

    return list(dedup.values())

def _build_richtungsrollen(docs: list[dict]) -> tuple[Dict[str, Dict[object, str]], str | None]:
    """
    Liest aus den vorhandenen dir-Docs die Rollen pro (Nachweis, Windrichtung) aus.
    Ergebnis: z.B. {"KIPP": {0.0: "relevant"}, "GLEIT": {90.0: "entscheidungsrelevant"}, ...}
    BALLAST übernimmt die Richtungsrollen des ballastkritischen Nachweises (quelle_nachweis).
    """
    rollen_by: Dict[str, Dict[object, str]] = {
        "KIPP": {},
        "GLEIT": {},
        "ABHEBE": {},
        "BALLAST": {},
    }
    ballast_source: str | None = None

    # 1) Rollen aus Richtungs-Top-Level-Docs für KIPP / GLEIT / ABHEBE auslesen
    for d in docs:
        ctx = d.get("context") or {}
        nachweis = ctx.get("nachweis")
        doc_type = ctx.get("doc_type")
        wdir = ctx.get("windrichtung_deg")
        rolle = ctx.get("rolle") or ctx.get("role")

        if wdir is None:
            continue
        if rolle is not None:
            rolle = str(rolle).lower()

        # GLEIT / ABHEBE: dir_sicherheit ist die "Richtungszusammenfassung"
        if nachweis == "GLEIT" and doc_type == "dir_sicherheit" and rolle:
            rollen_by["GLEIT"][wdir] = rolle

        if nachweis == "ABHEBE" and doc_type == "dir_sicherheit" and rolle:
            rollen_by["ABHEBE"][wdir] = rolle

        # KIPP: dir_min_sicherheit ist die maßgebende Richtungsinfo
        if nachweis == "KIPP" and doc_type == "dir_min_sicherheit" and rolle:
            rollen_by["KIPP"][wdir] = rolle

        # Ballast-Dokument: merkt sich nur, welcher Nachweis den Ballast bestimmt
        if nachweis == "BALLAST" and ballast_source is None:
            qs = ctx.get("quelle_nachweis")
            if qs in ("KIPP", "GLEIT", "ABHEBE"):
                ballast_source = qs

    # 2) BALLAST-Richtungsrollen = Rollen des ballastkritischen Nachweises
    if ballast_source:
        src_map = rollen_by.get(ballast_source, {})
        dst_map = rollen_by["BALLAST"]
        for wdir, rolle in src_map.items():
            dst_map[wdir] = rolle

    return rollen_by, ballast_source

def _annotate_rolle_pro_nachweis(docs: list[dict]) -> None:
    """
    Schreibt für jedes Doc eine vollständige Map rolle_pro_nachweis in den Kontext.

    - Grundlage ist IMMER die Rolle, die die Rechenfunktionen in ctx["rolle"] gesetzt haben.
    - Für LOADS (und nachweislose Meta-Docs) werden Rollen pro Nachweis aus den
      Richtungsrollen abgeleitet:
        * Nur die kritische Richtung (rolle == "relevant") wird als relevant gezogen.
        * Alles andere bleibt für diesen Nachweis "irrelevant".
    - Für BALLAST werden zusätzlich der ballastkritische Nachweis und die zugehörigen
      Sicherheitswerte sichtbar gemacht.
    """
    rollen_by, ballast_source = _build_richtungsrollen(docs)

    for d in docs:
        ctx = d.get("context") or {}
        wdir = ctx.get("windrichtung_deg")
        nachweis_doc = ctx.get("nachweis")
        own_role = (ctx.get("rolle") or ctx.get("role"))
        own_role = str(own_role).lower() if own_role is not None else None

        # Grundgerüst: jedes Doc bekommt alle vier Einträge
        rel_map: Dict[str, str] = {
            "KIPP": "irrelevant",
            "GLEIT": "irrelevant",
            "ABHEBE": "irrelevant",
            "BALLAST": "irrelevant",
        }

        # --- 1) Rolle für den "eigenen" Nachweis -----------------------
        if nachweis_doc in ("KIPP", "GLEIT", "ABHEBE"):
            # Hier vertrauen wir komplett der Rechenfunktion:
            # nur wo ctx.rolle gesetzt ist, war der Wert im Vergleich / Pfad.
            if own_role in ("relevant", "entscheidungsrelevant"):
                rel_map[nachweis_doc] = own_role

        elif nachweis_doc == "BALLAST":
            if own_role in ("relevant", "entscheidungsrelevant"):
                rel_map["BALLAST"] = own_role

        # --- 2) LOADS / globale Meta-Daten: Rollen über Richtungsrollen -------
        # LOADS und nachweislose Docs sollen die kritische Richtung pro Nachweis mitziehen.
        if nachweis_doc in ("LOADS", None) and wdir is not None:
            for nz in ("KIPP", "GLEIT", "ABHEBE"):
                rolle_dir = rollen_by.get(nz, {}).get(wdir)
                # Nur die wirklich kritische Richtung (rolle == "relevant") als relevant ziehen.
                if isinstance(rolle_dir, str) and rolle_dir.lower() == "relevant":
                    rel_map[nz] = "relevant"

            # BALLAST-Sicht für LOADS: gleiche Windrichtung wie ballastkritischer Nachweis
            if ballast_source and wdir is not None:
                rolle_dir = rollen_by.get(ballast_source, {}).get(wdir)
                if isinstance(rolle_dir, str) and rolle_dir.lower() == "relevant":
                    rel_map["BALLAST"] = "relevant"

        # --- 3) BALLAST-Sicht: Nachweis, der den Ballast liefert -------------
        # Alle Sicherheits-/Ballast-Dokumente des ballastkritischen Nachweises
        # sind auch für BALLAST relevant/entscheidungsrelevant.
        if ballast_source and nachweis_doc == ballast_source:
            if own_role in ("relevant", "entscheidungsrelevant"):
                rel_map["BALLAST"] = own_role

        # Kontext mit rolle_pro_nachweis zurückschreiben
        new_ctx = dict(ctx)
        new_ctx["rolle_pro_nachweis"] = rel_map
        d["context"] = new_ctx

# ====== Eingaben Meta ======
_DENY_KEYS = {
    "headers", "header", "authorization", "auth", "token", "csrf_token",
    "client", "user_agent", "cookies", "session", "trace_id", "request_id"
}
def _make_meta_eingaben(payload: Mapping[str, Any]) -> Dict[str, Any]:
    """
    Baut die meta.eingaben dynamisch aus dem tatsächlichen input_payload.
    - filtert offensichtliche Transport-/Security-Felder (Blacklist),
    - normalisiert Enums/Dataclasses/Iterables via _to_primitive,
    - hebt Zahlen JSON-sicher (NaN/INF) via _jsonify_number.
    """
    if not isinstance(payload, Mapping):
        return {}
    out: Dict[str, Any] = {}
    for k, v in payload.items():
        # Blacklist
        if k in _DENY_KEYS:
            continue
        # Zahlen gezielt über _jsonify_number, sonst generisch
        if isinstance(v, (int, float)):
            out[k] = _jsonify_number(v)
        else:
            out[k] = _to_primitive(v)
    return out

# ---------- main mapper ----------
def build_api_output(ergebnis, input_payload: Dict[str, Any]) -> Dict[str, Any]:
    """
    Mappt das reiche Ergebnisobjekt (z. B. StandsicherheitErgebnis) auf das API-Ausgabeformat:
      {
        "normen": {
          "EN_17879_2024": {
            "kipp": <float|"INF"|"-INF"|None>,
            "gleit": ...,
            "abhebe": ...,
            "ballast": ...,
            "alternativen": {
               "IN_BETRIEB": { ... }, ...
            },
            "messages": [
              {"severity":"warn","text":"...","code":"...","context":{"szenario":"IN_BETRIEB", ...}},
              ...
            ]
            "docs": [
                {
                "title": "Gleit-Aggregate (Richtung)",
                "value": null,
                "items": [["|T|_sum", 123.4], ["N_down_sum", 456.7], ...],
                "context": {
                    "nachweis": "GLEIT",
                    "doc_type": "dir_aggregate",
                    "windrichtung_deg": 270.0,
                    "rolle": "entscheidungsrelevant"
                }
            },
          },
          ...
        },
        "meta": {...}
      }
    WICHTIG: Werte bleiben wie bisher (float/None/"INF"/"-INF").
    Zusätzlich geben wir je Norm eine flache Liste "messages" zurück (Text, Severity, Kontext).
    """
    out_normen: Dict[str, Dict[str, Any]] = {}

    for norm, nres in ergebnis.normen.items():
        key = _NORM_KEY.get(norm)
        if not key:
            continue

        # --- numeric main values (unchanged behavior) ---
        main = {
            "kipp":    _jsonify_number(nres.werte.get(Nachweis.KIPP).wert)    if Nachweis.KIPP    in nres.werte else None,
            "gleit":   _jsonify_number(nres.werte.get(Nachweis.GLEIT).wert)   if Nachweis.GLEIT   in nres.werte else None,
            "abhebe":  _jsonify_number(nres.werte.get(Nachweis.ABHEBE).wert)  if Nachweis.ABHEBE  in nres.werte else None,
            "ballast": _jsonify_number(nres.werte.get(Nachweis.BALLAST).wert) if Nachweis.BALLAST in nres.werte else None,
        }

        # --- alternatives (same handling for numbers) ---
        alts: Dict[str, Dict[str, float | str | None]] = {}
        for alt_name, alt_res in (nres.alternativen or {}).items():
            vals = getattr(alt_res, "werte", {}) or {}

            alts[alt_name] = {
                "anzeigename": getattr(alt_res, "anzeigename", alt_name),

                "kipp":    _jsonify_number(vals.get(Nachweis.KIPP).wert)    if Nachweis.KIPP    in vals else None,
                "gleit":   _jsonify_number(vals.get(Nachweis.GLEIT).wert)   if Nachweis.GLEIT   in vals else None,
                "abhebe":  _jsonify_number(vals.get(Nachweis.ABHEBE).wert)  if Nachweis.ABHEBE  in vals else None,
                "ballast": _jsonify_number(vals.get(Nachweis.BALLAST).wert) if Nachweis.BALLAST in vals else None,
            }
        if alts:
            main["alternativen"] = alts

        # --- messages per norm (flat list) ---
        messages = []

        # 1) norm-level reasons
        messages += _collect_messages_from_list(getattr(nres, "reasons", None))

        # 2) SafetyValue.messages on main values (if you attach messages to values)
        for nachweis in (Nachweis.KIPP, Nachweis.GLEIT, Nachweis.ABHEBE, Nachweis.BALLAST):
            if nachweis in nres.werte:
                sv = nres.werte[nachweis]
                # we add nachweis to context if missing
                msgs = _collect_messages_from_list(
                    getattr(sv, "messages", None)
                )
                # ensure nachweis key is in context for these
                for m in msgs:
                    m["context"] = dict(m["context"] or {})
                    m["context"].setdefault("nachweis", _enum_to_str(nachweis))
                messages += msgs

        # 3) messages attached to alternatives' values
        for alt_name, alt_res in (nres.alternativen or {}).items():
            vals = getattr(alt_res, "werte", {}) or {}
            for nachweis, sv in vals.items():
                msgs = _collect_messages_from_list(
                    getattr(sv, "messages", None),
                    fallback_szenario=alt_name
                )
                for m in msgs:
                    m["context"] = dict(m["context"] or {})
                    m["context"].setdefault("nachweis", _enum_to_str(nachweis))
                    m["context"].setdefault("szenario", alt_name)
                messages += msgs

        # 4) optional: details.notes
        details = getattr(nres, "details", None)
        if details is not None:
            messages += _collect_messages_from_list(getattr(details, "notes", None))

         # ========= NEU: Messages in Haupt vs. Alternativen splitten =========
        messages_main: list[dict] = []
        alt_msgs_map: Dict[str, list[dict]] = { name: [] for name in (alts.keys() if alts else []) }
        if messages:
            alt_names = set(alts.keys())
            for m in messages:
                ctx = m.get("context") or {}
                sc = ctx.get("szenario") or ctx.get("scenario")
                sc = None if sc is None else str(sc).strip()
                if sc in alt_names:
                    alt_msgs_map[sc].append(m)
                else:
                    messages_main.append(m)
        # ====================================================================

        # --- docs per norm (Zwischenergebnisse) ---
        docs_main: list[dict] = []
        alt_docs_map: Dict[str, list[dict]] = { name: [] for name in (alts.keys() if alts else []) }

        details = getattr(nres, "details", None)
        if details is not None:
            raw_docs = getattr(details, "docs", None)  # erwartet: List[(bundle, ctx)]
            if raw_docs:
                docs_all = _collect_docs_from_list(raw_docs)
                # ========= NEU: Docs in Haupt vs. Alternativen splitten =========
                alt_names = set(alts.keys())
                for d in docs_all:
                    ctx = d.get("context") or {}
                    sc = ctx.get("szenario") or ctx.get("scenario")
                    sc = None if sc is None else str(sc).strip()
                    if sc in alt_names:
                        alt_docs_map[sc].append(d)
                    else:
                        docs_main.append(d)
                # ========= NEU: Relevanz pro Nachweis je Doc berechnen =========
                if docs_main:
                    _annotate_rolle_pro_nachweis(docs_main)
                if alt_docs_map:
                    for name, docs_list in alt_docs_map.items():
                        if docs_list:
                            _annotate_rolle_pro_nachweis(docs_list)
                # ===============================================================

        # --- attach split messages/docs to alternatives ---
        if alts:
            for name in alts.keys():
                alts[name]["messages"] = alt_msgs_map.get(name, [])
                alts[name]["docs"] = alt_docs_map.get(name, [])

        out_normen[key] = { **main, "messages": messages_main, "docs": docs_main }

    # ---- meta unchanged ----
    return {
        "normen": out_normen,
        "meta": {
            "version": ergebnis.meta.version,
            "eingaben": _make_meta_eingaben(input_payload),
        },
    }
