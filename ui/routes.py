from flask import Blueprint, render_template, request, jsonify

# Create Blueprint
ui_bp = Blueprint("ui", __name__, template_folder="templates", static_folder="static")


@ui_bp.route("/")
def index():
    """Render the main UI page."""
    return render_template("index.html")
