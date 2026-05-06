# DEBUG_ergebnisobjekt.py

from __future__ import annotations

import json
import math
from dataclasses import asdict, is_dataclass
from enum import Enum
from pathlib import Path
from typing import Any


# ============================================================
# JSON SERIALIZATION
# ============================================================


def _json_safe(value: Any) -> Any:
    """
    Macht Werte JSON-kompatibel.

    Wichtig:
    - Infinity / -Infinity / NaN existieren offiziell nicht in JSON.
    - Wir serialisieren sie daher als Strings.
    """

    if isinstance(value, float):
        if math.isinf(value):
            return "Infinity" if value > 0 else "-Infinity"
        if math.isnan(value):
            return "NaN"
        return value

    if isinstance(value, Enum):
        return value.name

    if is_dataclass(value):
        return _json_safe(asdict(value))

    if isinstance(value, dict):
        return {
            str(_json_safe(k)): _json_safe(v)
            for k, v in value.items()
        }

    if isinstance(value, (list, tuple)):
        return [_json_safe(v) for v in value]

    return value


# ============================================================
# COMPACT SERIALIZATION
# ============================================================


def tree_to_compact_jsonable(obj: Any) -> Any:
    """
    Baut eine kompakte JSON-Struktur:
    - entfernt None
    - entfernt leere Listen
    - entfernt leere Dicts
    - entfernt leere Strings
    - serialisiert Infinity/NaN sicher
    """

    def clean(x: Any) -> Any:
        x = _json_safe(x)

        if isinstance(x, dict):
            out = {}
            for k, v in x.items():
                cv = clean(v)
                if cv in (None, {}, [], ""):
                    continue
                out[k] = cv
            return out

        if isinstance(x, list):
            out = [clean(v) for v in x]
            return [v for v in out if v not in (None, {}, [], "")]

        return x

    return clean(obj)


# ============================================================
# SAVE HELPERS
# ============================================================


def save_tree_json(
    tree: Any,
    pfad: str = "ergebnisbaum.json",
    *,
    compact: bool = True,
) -> None:
    """
    Speichert den Ergebnisbaum als JSON.

    compact=True:
        Entfernt leere/default Felder.

    compact=False:
        Vollständiger Dump.
    """

    path = Path(pfad)
    path.parent.mkdir(parents=True, exist_ok=True)

    data = tree_to_compact_jsonable(tree) if compact else _json_safe(tree)

    path.write_text(
        json.dumps(data, indent=2, ensure_ascii=False),
        encoding="utf-8",
    )

    print(f"✅ Ergebnisbaum gespeichert: {path.resolve()}")


# ============================================================
# TREE STATS
# ============================================================


def build_tree_stats_report(tree: Any) -> tuple[str, dict, list[tuple]]:
    """
    Analysiert die Baumgröße und gibt einen Textreport zurück.
    """

    stats = {
        "ebenen": 0,
        "gruppen": 0,
        "ergebnisse": 0,
        "messages": 0,
        "max_depth": 0,
        "result_names": {},
        "level_names": {},
    }

    suspicious: list[tuple] = []

    def inc(d: dict, key: str) -> None:
        d[key] = d.get(key, 0) + 1

    def walk_container(ebenen: list, path: list[str], depth: int) -> None:
        stats["max_depth"] = max(stats["max_depth"], depth)

        for ebene in ebenen:
            stats["ebenen"] += 1
            inc(stats["level_names"], ebene.name)

            for gruppe in ebene.gruppen:
                stats["gruppen"] += 1

                gpath = path + [f"{ebene.name}={gruppe.name}"]

                ergebnisse = getattr(gruppe, "ergebnisse", []) or []
                messages = getattr(gruppe, "messages", []) or []
                child_ebenen = getattr(gruppe, "ebenen", []) or []

                stats["ergebnisse"] += len(ergebnisse)
                stats["messages"] += len(messages)

                for e in ergebnisse:
                    inc(stats["result_names"], e.name)

                if len(child_ebenen) > 20:
                    suspicious.append((
                        "many_child_levels",
                        "/".join(gpath),
                        len(child_ebenen),
                    ))

                if len(ergebnisse) > 100:
                    suspicious.append((
                        "many_results",
                        "/".join(gpath),
                        len(ergebnisse),
                    ))

                if len(messages) > 50:
                    suspicious.append((
                        "many_messages",
                        "/".join(gpath),
                        len(messages),
                    ))

                walk_container(child_ebenen, gpath, depth + 1)

    root_ergebnisse = getattr(tree, "ergebnisse", []) or []
    root_messages = getattr(tree, "messages", []) or []
    root_ebenen = getattr(tree, "ebenen", []) or []

    stats["ergebnisse"] += len(root_ergebnisse)
    stats["messages"] += len(root_messages)

    walk_container(root_ebenen, [], 0)

    lines: list[str] = []
    lines.append("TREE STATS")
    lines.append("===========")

    for k in (
        "ebenen",
        "gruppen",
        "ergebnisse",
        "messages",
        "max_depth",
    ):
        lines.append(f"{k}: {stats[k]}")

    lines.append("")
    lines.append("Top result names:")
    for name, count in sorted(
        stats["result_names"].items(),
        key=lambda x: x[1],
        reverse=True,
    )[:30]:
        lines.append(f"{count:6}  {name}")

    lines.append("")
    lines.append("Top level names:")
    for name, count in sorted(
        stats["level_names"].items(),
        key=lambda x: x[1],
        reverse=True,
    )[:30]:
        lines.append(f"{count:6}  {name}")

    lines.append("")
    lines.append("Suspicious:")
    if suspicious:
        for item in suspicious[:50]:
            lines.append(str(item))
    else:
        lines.append("- keine auffälligen Knoten gefunden")

    return "\n".join(lines), stats, suspicious


def debug_tree_stats(tree: Any, *, output_path: str | None = None) -> tuple[dict, list[tuple]]:
    """
    Analysiert die Baumgröße.

    Wenn output_path gesetzt ist, wird der Report in eine Datei geschrieben.
    Sonst wird er in die Konsole geschrieben.
    """

    report, stats, suspicious = build_tree_stats_report(tree)

    if output_path is not None:
        path = Path(output_path)
        path.parent.mkdir(parents=True, exist_ok=True)
        path.write_text(report, encoding="utf-8")
        print(f"✅ Tree-Stats gespeichert: {path.resolve()}")
    else:
        print(report)

    return stats, suspicious


# ============================================================
# TREE OUTLINE
# ============================================================


def build_tree_outline(
    tree: Any,
    *,
    max_depth: int = 8,
    only_nonempty: bool = True,
) -> str:
    """
    Baut eine kompakte Baumübersicht als String.
    """

    lines: list[str] = []

    def walk(ebenen: list, indent: int = 0, depth: int = 0) -> None:
        if depth > max_depth:
            return

        for ebene in ebenen:
            for gruppe in ebene.gruppen:
                ergebnisse = getattr(gruppe, "ergebnisse", []) or []
                messages = getattr(gruppe, "messages", []) or []
                child_ebenen = getattr(gruppe, "ebenen", []) or []

                has_content = bool(ergebnisse or messages)
                has_children = bool(child_ebenen)

                if not only_nonempty or has_content or has_children:
                    marker = []

                    if getattr(gruppe, "winner", False):
                        marker.append("winner")

                    if ergebnisse:
                        marker.append(f"{len(ergebnisse)} results")

                    if messages:
                        marker.append(f"{len(messages)} msgs")

                    suffix = f"  [{' | '.join(marker)}]" if marker else ""
                    lines.append("  " * indent + f"{ebene.name}={gruppe.name}{suffix}")

                walk(child_ebenen, indent + 1, depth + 1)

    lines.append("ROOT")

    root_ergebnisse = getattr(tree, "ergebnisse", []) or []
    root_messages = getattr(tree, "messages", []) or []

    if root_ergebnisse:
        lines.append(f"  root results: {len(root_ergebnisse)}")

    if root_messages:
        lines.append(f"  root messages: {len(root_messages)}")

    walk(getattr(tree, "ebenen", []) or [])

    return "\n".join(lines)


def print_tree_outline(
    tree: Any,
    *,
    max_depth: int = 8,
    only_nonempty: bool = True,
    output_path: str | None = None,
) -> None:
    """
    Druckt oder speichert eine kompakte Baumübersicht.
    """

    outline = build_tree_outline(
        tree,
        max_depth=max_depth,
        only_nonempty=only_nonempty,
    )

    if output_path is not None:
        path = Path(output_path)
        path.parent.mkdir(parents=True, exist_ok=True)
        path.write_text(outline, encoding="utf-8")
        print(f"✅ Tree-Outline gespeichert: {path.resolve()}")
    else:
        print(outline)


# ============================================================
# QUICK DEBUG ENTRYPOINT
# ============================================================


def debug_tree(
    tree: Any,
    *,
    save_json: bool = True,
    compact_json: bool = True,
    json_path: str = "ergebnisbaum_debug.json",
    print_outline: bool = True,
    print_stats: bool = True,
    output_dir: str = "debug_output",
) -> None:
    """
    Einmal alles für schnelles Debugging.

    Schreibt standardmäßig in:
        debug_output/
            ergebnisbaum_debug.json
            tree_outline.txt
            tree_stats.txt
    """

    out_dir = Path(output_dir)
    out_dir.mkdir(parents=True, exist_ok=True)

    if save_json:
        save_tree_json(
            tree,
            pfad=str(out_dir / json_path),
            compact=compact_json,
        )

    if print_outline:
        print_tree_outline(
            tree,
            output_path=str(out_dir / "tree_outline.txt"),
        )

    if print_stats:
        debug_tree_stats(
            tree,
            output_path=str(out_dir / "tree_stats.txt"),
        )