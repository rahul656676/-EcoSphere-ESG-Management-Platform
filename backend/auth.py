"""
EcoSphere - auth.py
Simple session-based authentication (username/password + Flask session cookie).
Default admin credentials: admin / admin123 (change in Settings after first login).
"""

import time
from functools import wraps
from flask import Blueprint, request, jsonify, session
from werkzeug.security import generate_password_hash, check_password_hash

import models

auth_bp = Blueprint("auth", __name__)

DEFAULT_ADMIN_USER = "admin"
DEFAULT_ADMIN_PASS = "admin123"

# Basic in-memory rate limiter for login
FAILED_LOGINS = {}
LOCKOUT_TIME = 60  # seconds
MAX_ATTEMPTS = 5


def ensure_default_admin():
    row = models.query("SELECT * FROM users WHERE username = ?", (DEFAULT_ADMIN_USER,), one=True)
    pw_hash = generate_password_hash(DEFAULT_ADMIN_PASS)
    if row is None:
        models.insert_row("users", {
            "username": DEFAULT_ADMIN_USER,
            "password_hash": pw_hash,
            "role": "Admin",
            "employee_id": 6,
        })
    else:
        # Reset placeholder hash inserted by seed.sql on first boot
        if row["password_hash"].startswith("pbkdf2:sha256:600000$placeholder"):
            models.update_row("users", row["id"], {"password_hash": pw_hash})


def login_required(f):
    @wraps(f)
    def wrapper(*args, **kwargs):
        if not session.get("user_id"):
            return jsonify({"error": "Authentication required"}), 401
        return f(*args, **kwargs)
    return wrapper


@auth_bp.route("/api/auth/login", methods=["POST"])
def login():
    ip = request.remote_addr
    now = time.time()
    
    # Rate limit check
    if ip in FAILED_LOGINS:
        attempts, last_time = FAILED_LOGINS[ip]
        if attempts >= MAX_ATTEMPTS:
            if now - last_time < LOCKOUT_TIME:
                return jsonify({"success": False, "error": "Too many failed attempts. Try again later."}), 429
            else:
                FAILED_LOGINS[ip] = [0, now]

    data = request.get_json(force=True, silent=True) or {}
    username = data.get("username", "")
    password = data.get("password", "")

    user = models.query("SELECT * FROM users WHERE username = ?", (username,), one=True)
    if user and check_password_hash(user["password_hash"], password):
        if ip in FAILED_LOGINS:
            del FAILED_LOGINS[ip]
        session["user_id"] = user["id"]
        session["username"] = user["username"]
        session["role"] = user["role"]
        return jsonify({"success": True, "user": {
            "id": user["id"], "username": user["username"], "role": user["role"]
        }})
        
    # Record failure
    if ip not in FAILED_LOGINS:
        FAILED_LOGINS[ip] = [1, now]
    else:
        FAILED_LOGINS[ip][0] += 1
        FAILED_LOGINS[ip][1] = now

    return jsonify({"success": False, "error": "Invalid username or password"}), 401


@auth_bp.route("/api/auth/logout", methods=["POST"])
def logout():
    session.clear()
    return jsonify({"success": True})


@auth_bp.route("/api/auth/me", methods=["GET"])
def me():
    if not session.get("user_id"):
        return jsonify({"authenticated": False})
    return jsonify({
        "authenticated": True,
        "username": session.get("username"),
        "role": session.get("role"),
    })
