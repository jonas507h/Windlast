from flask import jsonify, Response
from . import bp_v1

from pathlib import Path
import markdown

from windlast_API.utils.files import get_project_root


@bp_v1.get("/meta/changelog")
def get_changelog():
    root = get_project_root()
    changelog_path = root / "CHANGELOG.md"

    if not changelog_path.exists():
        return jsonify({"error": "CHANGELOG.md nicht gefunden"}), 404

    md_text = changelog_path.read_text(encoding="utf-8")

    html = markdown.markdown(
        md_text,
        extensions=[
            "extra",        # Tabellen, Listen, etc.
            "sane_lists"
        ]
    )

    return Response(html, mimetype="text/html")
