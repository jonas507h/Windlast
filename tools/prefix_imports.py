from __future__ import annotations
import argparse
from pathlib import Path
import re
import sys

# Ordner mit deinen Core-Modulen
CORE_ROOT = Path(__file__).resolve().parents[1] / "windlast_CORE"

# Top-Level-Paketnamen innerhalb von windlast_CORE, die oft flach importiert werden:
TARGETS = ("datenstruktur", "bauelemente", "konstruktionen", "materialdaten", "rechenfunktionen", "core_adapter")

# Regexe:
# 1) from <pkg>(.sub)* import ...
re_from = re.compile(
    rf'^(?P<indent>\s*)from\s+(?P<pkg>(?:{"|".join(TARGETS)})(?:\.[\w_]+)*)\s+import\s+(?P<rest>.+)$',
    re.MULTILINE,
)

# 2) import <pkg>(.sub)*( as alias)?, (weiteres Paket ...), ...
#    -> wir gehen Paket-für-Paket durch und präfixen jeweils, wenn nötig.
re_import_line = re.compile(r'^(?P<indent>\s*)import\s+(?P<rest>.+)$', re.MULTILINE)

def prefix_pkg(name: str) -> str:
    # bereits absolut?
    if name.startswith("windlast_CORE."):
        return name
    first = name.split(".")[0]
    if first in TARGETS:
        return f"windlast_CORE.{name}"
    return name

def transform_from(line: str) -> str:
    m = re_from.match(line)
    if not m:
        return line
    pkg = m.group("pkg")
    prefixed = prefix_pkg(pkg)
    if prefixed == pkg:
        return line
    return f'{m.group("indent")}from {prefixed} import {m.group("rest")}'

def transform_import(line: str) -> str:
    m = re_import_line.match(line)
    if not m:
        return line
    indent, rest = m.group("indent"), m.group("rest")
    # Split an Kommas, aber Respekt vor " as ":
    parts = [p.strip() for p in rest.split(",")]
    new_parts = []
    changed = False
    for p in parts:
        # Beispiele: "datenstruktur.konstanten", "bauelemente.bodenplatte as bp"
        if " as " in p:
            mod, alias = p.split(" as ", 1)
            new_mod = prefix_pkg(mod.strip())
            new_parts.append(f"{new_mod} as {alias.strip()}")
            if new_mod != mod.strip():
                changed = True
        else:
            new_mod = prefix_pkg(p)
            new_parts.append(new_mod)
            if new_mod != p:
                changed = True
    if not changed:
        return line
    return f'{indent}import {", ".join(new_parts)}'

def process_file(path: Path) -> tuple[bool, str]:
    text = path.read_text(encoding="utf-8")
    new = text

    # erst "from … import …", dann "import …"
    new = re_from.sub(lambda m: transform_from(m.group(0)), new)
    new = re_import_line.sub(lambda m: transform_import(m.group(0)), new)

    return (new != text, new)

def ensure_inits():
    # sorgt dafür, dass alle Ordner in windlast_CORE echte Pakete sind
    created = []
    for d in CORE_ROOT.rglob("*"):
        if d.is_dir():
            init_file = d / "__init__.py"
            if not init_file.exists():
                init_file.write_text("", encoding="utf-8")
                created.append(init_file)
    return created

def main():
    if not CORE_ROOT.exists():
        print(f"[error] CORE_ROOT nicht gefunden: {CORE_ROOT}", file=sys.stderr)
        sys.exit(1)

    parser = argparse.ArgumentParser(description="Prefix flache Importe mit 'windlast_CORE.'")
    parser.add_argument("--apply", action="store_true", help="Änderungen schreiben (kein Dry-Run)")
    parser.add_argument("--no-init", action="store_true", help="keine __init__.py automatisch anlegen")
    args = parser.parse_args()

    if not args.no_init:
        created = ensure_inits()
        if created:
            print(f"[init] __init__.py angelegt in {len(created)} Ordnern")

    py_files = [p for p in CORE_ROOT.rglob("*.py") if "__pycache__" not in p.parts]

    changed_files = 0
    for f in py_files:
        changed, new_text = process_file(f)
        if changed:
            changed_files += 1
            print(f"[change] {f.relative_to(CORE_ROOT)}")
            if args.apply:
                f.write_text(new_text, encoding="utf-8")

    if not args.apply:
        print(f"\n[Dry-Run] {changed_files} Dateien würden geändert. Starte mit --apply, um zu schreiben.")

if __name__ == "__main__":
    main()
