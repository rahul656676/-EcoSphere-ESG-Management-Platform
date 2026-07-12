import pytest
import os
import sys
import tempfile

# Add backend directory to sys.path so we can import from it
sys.path.insert(0, os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))), "backend"))

from app import create_app
import models

@pytest.fixture
def client():
    # Use temporary file SQLite for testing to avoid touching production DB
    db_fd, db_path = tempfile.mkstemp()
    models.DB_PATH = db_path
    app = create_app()
    app.config["TESTING"] = True
    
    with app.test_client() as client:
        with app.app_context():
            # Init DB on the connection
            models.init_db(force=True)
            models.execute("INSERT INTO users (username, password_hash, role) VALUES ('testuser', 'pbkdf2:sha256:600000$placeholder', 'User')")
        yield client
        
    os.close(db_fd)
    os.unlink(db_path)

def test_login_failure(client):
    response = client.post("/api/auth/login", json={"username": "wrong", "password": "wrong"})
    assert response.status_code == 401
    assert b"Invalid username or password" in response.data

def test_unauthorized_access(client):
    response = client.get("/api/auth/me")
    assert response.status_code == 200
    assert response.get_json() == {"authenticated": False}
