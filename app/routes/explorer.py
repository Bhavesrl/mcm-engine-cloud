import os
from flask import Blueprint, send_from_directory

explorer_bp = Blueprint("explorer", __name__)

_DIST = os.path.abspath(
    os.path.join(os.path.dirname(__file__), "..", "..", "frontend", "dist")
)


@explorer_bp.route("/explorer/", defaults={"path": ""})
@explorer_bp.route("/explorer/<path:path>")
def serve(path):
    target = os.path.join(_DIST, path)
    if path and os.path.isfile(target):
        return send_from_directory(_DIST, path)
    return send_from_directory(_DIST, "index.html")
