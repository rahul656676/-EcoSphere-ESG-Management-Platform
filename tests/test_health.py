import pytest
import os
import sys
import tempfile
import uuid

# Add backend directory to sys.path so we can import from it
sys.path.insert(0, os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))), "backend"))

from app import create_app
import models

@pytest.fixture
def client():
    # Use temporary file SQLite for testing to avoid touching production DB
    db_path = os.path.join(tempfile.gettempdir(), f"test_{uuid.uuid4().hex}.db")
    models.DB_PATH = db_path
    app = create_app()
    app.config["TESTING"] = True
    
    with app.test_client() as client:
        with app.app_context():
            # Init DB on the connection
            models.init_db(force=True)
        yield client
        
    try:
        os.unlink(db_path)
    except:
        pass

def test_health_check(client):
    response = client.get("/api/health")
    assert response.status_code == 200
    data = response.get_json()
    assert data["status"] == "ok"
    assert data["database"] == "connected"
