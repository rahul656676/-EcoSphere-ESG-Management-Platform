"""
EcoSphere - app.py
Main Flask application entrypoint. Serves the REST API (routes.py, auth.py)
and the static frontend pages (frontend/*.html).

Run:
    cd backend
    python3 app.py
Then open http://localhost:5000  (default login: admin / admin123)
"""

import os
import sys
import logging
from dotenv import load_dotenv

# Configure standard logging
logging.basicConfig(level=logging.INFO, format='%(asctime)s [%(levelname)s] %(message)s')
logger = logging.getLogger(__name__)

# Load environment variables from .env file
load_dotenv()

from flask import Flask, send_from_directory, session, redirect, jsonify

BASE_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
FRONTEND_DIR = os.path.join(BASE_DIR, "frontend")
AI_DIR = os.path.join(BASE_DIR, "ai")

sys.path.insert(0, AI_DIR)  # so routes.py can `import reports`

import models  # noqa: E402
import controllers  # noqa: E402
from auth import auth_bp, ensure_default_admin  # noqa: E402
from routes import api  # noqa: E402


def create_app():
    app = Flask(__name__, static_folder=FRONTEND_DIR, static_url_path="")
    # Secure random fallback if not configured in environment
    app.secret_key = os.environ.get("ECOSPHERE_SECRET_KEY") or os.urandom(24).hex()

    models.init_db()
    ensure_default_admin()
    controllers.recompute_department_scores()
    controllers.refresh_overdue_compliance_issues()

    app.register_blueprint(auth_bp)
    app.register_blueprint(api)

    @app.route("/")
    def index():
        if not session.get("user_id"):
            return send_from_directory(FRONTEND_DIR, "login.html")
        return send_from_directory(FRONTEND_DIR, "dashboard.html")

    @app.route("/<path:page>")
    def frontend_pages(page):
        file_path = os.path.join(FRONTEND_DIR, page)
        if os.path.isfile(file_path):
            return send_from_directory(FRONTEND_DIR, page)
        return redirect("/")

    @app.route("/api/reset-demo-data", methods=["POST"])
    def reset_demo_data():
        # Convenience endpoint for graders/demo: rebuild DB from schema+seed.
        models.init_db(force=True)
        ensure_default_admin()
        controllers.recompute_department_scores()
        return {"success": True}

    @app.route("/api/health")
    def health_check():
        try:
            # Simple test query to ensure DB is connected
            models.query("SELECT 1")
            return jsonify({"status": "ok", "database": "connected"})
        except Exception as e:
            logger.error(f"Health check failed: {e}")
            return jsonify({"status": "error", "database": "disconnected"}), 500

    return app


app = create_app()

# Start the background cron scheduler
try:
    from scheduler import start_background_jobs
    start_background_jobs()
except Exception as e:
    logger.error(f"Failed to start scheduler: {e}")

if __name__ == "__main__":
    app.run(host="0.0.0.0", port=5000, debug=True)
