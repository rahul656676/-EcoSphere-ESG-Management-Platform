"""
EcoSphere - routes.py
REST API endpoints for all modules: Dashboard, Environmental, Social,
Governance, Gamification, Reports, Settings.
"""

from flask import Blueprint, request, jsonify
import models
import controllers
from auth import login_required

api = Blueprint("api", __name__, url_prefix="/api")


def crud_routes(bp, name, table, editable_fields):
    """Registers generic GET-all / GET-one / POST / PUT / DELETE for a table."""

    @bp.route(f"/{name}", methods=["GET"], endpoint=f"{name}_list")
    @login_required
    def list_all():
        return jsonify(models.table_all(table))

    @bp.route(f"/{name}/<int:row_id>", methods=["GET"], endpoint=f"{name}_get")
    @login_required
    def get_one(row_id):
        row = models.get_by_id(table, row_id)
        if not row:
            return jsonify({"error": "Not found"}), 404
        return jsonify(row)

    @bp.route(f"/{name}", methods=["POST"], endpoint=f"{name}_create")
    @login_required
    def create():
        data = request.get_json(force=True, silent=True) or {}
        payload = {k: v for k, v in data.items() if k in editable_fields}
        new_id = models.insert_row(table, payload)
        return jsonify({"success": True, "id": new_id}), 201

    @bp.route(f"/{name}/<int:row_id>", methods=["PUT"], endpoint=f"{name}_update")
    @login_required
    def update(row_id):
        data = request.get_json(force=True, silent=True) or {}
        payload = {k: v for k, v in data.items() if k in editable_fields}
        models.update_row(table, row_id, payload)
        return jsonify({"success": True})

    @bp.route(f"/{name}/<int:row_id>", methods=["DELETE"], endpoint=f"{name}_delete")
    @login_required
    def delete(row_id):
        models.delete_row(table, row_id)
        return jsonify({"success": True})


# ---------------------------------------------------------------------------
# Settings / Master Data - generic CRUD
# ---------------------------------------------------------------------------

crud_routes(api, "departments", "department",
            ["name", "code", "head", "parent_department_id", "employee_count", "status"])

crud_routes(api, "categories", "category", ["name", "type", "status"])

crud_routes(api, "emission-factors", "emission_factor",
            ["name", "source_type", "unit", "co2_factor", "status"])

crud_routes(api, "product-profiles", "product_esg_profile",
            ["product_name", "category", "co2_per_unit", "notes"])

crud_routes(api, "environmental-goals", "environmental_goal",
            ["name", "department_id", "target_co2", "current_co2", "deadline", "status"])

crud_routes(api, "policies", "esg_policy",
            ["title", "description", "department_id", "status", "created_date"])

crud_routes(api, "badges", "badge",
            ["name", "description", "unlock_rule_type", "unlock_rule_value", "icon"])

crud_routes(api, "rewards", "reward",
            ["name", "description", "points_required", "stock", "status"])

crud_routes(api, "employees", "employee",
            ["name", "email", "department_id", "xp_total", "points_balance", "gender", "role"])

crud_routes(api, "csr-activities", "csr_activity",
            ["name", "category_id", "description", "date", "evidence_required", "status"])

crud_routes(api, "challenges", "challenge",
            ["title", "category_id", "description", "xp", "difficulty",
             "evidence_required", "deadline", "status"])

crud_routes(api, "audits", "audit",
            ["title", "department_id", "auditor", "date", "findings", "status"])


# ---------------------------------------------------------------------------
# Carbon Transactions (with Auto Emission Calculation business rule)
# ---------------------------------------------------------------------------

@api.route("/carbon-transactions", methods=["GET"])
@login_required
def list_carbon_transactions():
    return jsonify(models.query("""
        SELECT ct.*, d.name AS department_name, ef.name AS emission_factor_name
        FROM carbon_transaction ct
        LEFT JOIN department d ON ct.department_id = d.id
        LEFT JOIN emission_factor ef ON ct.emission_factor_id = ef.id
        ORDER BY ct.date DESC
    """))


import csv
import io

@api.route("/transactions/import", methods=["POST"])
@login_required
def import_transactions():
    if 'file' not in request.files:
        return jsonify({"success": False, "error": "No file part"}), 400
    file = request.files['file']
    if file.filename == '':
        return jsonify({"success": False, "error": "No selected file"}), 400
    
    if not file.filename.endswith('.csv'):
        return jsonify({"success": False, "error": "Only CSV files are supported"}), 400
        
    try:
        stream = io.StringIO(file.stream.read().decode("UTF8"), newline=None)
        csv_input = csv.DictReader(stream)
        
        imported_count = 0
        for row in csv_input:
            # Expected columns: department_id, source_type, emission_factor_id, quantity, remarks
            dept_id = int(row.get('department_id', 0))
            factor_id = int(row.get('emission_factor_id', 0))
            qty = float(row.get('quantity', 0))
            source = row.get('source_type', 'Purchase')
            remarks = row.get('remarks', 'Imported via CSV')
            
            if dept_id > 0 and factor_id > 0 and qty > 0:
                from controllers import calculate_emission
                calculate_emission(dept_id, source, factor_id, qty, remarks)
                imported_count += 1
                
        return jsonify({"success": True, "message": f"Successfully imported {imported_count} transactions."})
    except Exception as e:
        return jsonify({"success": False, "error": str(e)}), 400


@api.route("/carbon-transactions", methods=["POST"])
@login_required
def create_carbon_transaction():
    data = request.get_json(force=True, silent=True) or {}
    txn_id = controllers.calculate_emission(
        department_id=data.get("department_id"),
        source_type=data.get("source_type"),
        emission_factor_id=data.get("emission_factor_id"),
        quantity=float(data.get("quantity", 0)),
        remarks=data.get("remarks", ""),
    )
    return jsonify({"success": True, "id": txn_id}), 201


# ---------------------------------------------------------------------------
# Employee Participation (CSR) - Evidence Requirement + Approval workflow
# ---------------------------------------------------------------------------

@api.route("/employee-participation", methods=["GET"])
@login_required
def list_employee_participation():
    return jsonify(models.query("""
        SELECT ep.*, e.name AS employee_name, ca.name AS activity_name
        FROM employee_participation ep
        JOIN employee e ON ep.employee_id = e.id
        JOIN csr_activity ca ON ep.activity_id = ca.id
        ORDER BY ep.id DESC
    """))


@api.route("/employee-participation", methods=["POST"])
@login_required
def create_employee_participation():
    data = request.get_json(force=True, silent=True) or {}
    new_id = models.insert_row("employee_participation", {
        "employee_id": data.get("employee_id"),
        "activity_id": data.get("activity_id"),
        "proof_file": data.get("proof_file"),
        "approval_status": "Pending",
        "points_earned": data.get("points_earned", 0),
        "completion_date": None,
    })
    return jsonify({"success": True, "id": new_id}), 201


@api.route("/employee-participation/<int:pid>/decision", methods=["POST"])
@login_required
def decide_employee_participation(pid):
    data = request.get_json(force=True, silent=True) or {}
    result, code = controllers.approve_employee_participation(pid, data.get("decision"))
    return jsonify(result), code


# ---------------------------------------------------------------------------
# Challenge Participation - Evidence Requirement + XP Award workflow
# ---------------------------------------------------------------------------

@api.route("/challenge-participation", methods=["GET"])
@login_required
def list_challenge_participation():
    return jsonify(models.query("""
        SELECT cp.*, e.name AS employee_name, c.title AS challenge_title
        FROM challenge_participation cp
        JOIN employee e ON cp.employee_id = e.id
        JOIN challenge c ON cp.challenge_id = c.id
        ORDER BY cp.id DESC
    """))


@api.route("/challenge-participation", methods=["POST"])
@login_required
def create_challenge_participation():
    data = request.get_json(force=True, silent=True) or {}
    new_id = models.insert_row("challenge_participation", {
        "challenge_id": data.get("challenge_id"),
        "employee_id": data.get("employee_id"),
        "progress": data.get("progress", 0),
        "proof_file": data.get("proof_file"),
        "approval_status": "Pending",
        "xp_awarded": 0,
    })
    return jsonify({"success": True, "id": new_id}), 201


@api.route("/challenge-participation/<int:pid>/decision", methods=["POST"])
@login_required
def decide_challenge_participation(pid):
    data = request.get_json(force=True, silent=True) or {}
    result, code = controllers.approve_challenge_participation(pid, data.get("decision"))
    return jsonify(result), code


# ---------------------------------------------------------------------------
# Policy Acknowledgements
# ---------------------------------------------------------------------------

@api.route("/policy-acknowledgements", methods=["GET"])
@login_required
def list_policy_ack():
    return jsonify(models.query("""
        SELECT pa.*, e.name AS employee_name, p.title AS policy_title
        FROM policy_acknowledgement pa
        JOIN employee e ON pa.employee_id = e.id
        JOIN esg_policy p ON pa.policy_id = p.id
        ORDER BY pa.id DESC
    """))


@api.route("/policy-acknowledgements/<int:pid>/acknowledge", methods=["POST"])
@login_required
def acknowledge_policy(pid):
    from datetime import date
    models.update_row("policy_acknowledgement", pid, {
        "status": "Acknowledged", "acknowledged_date": date.today().isoformat()
    })
    return jsonify({"success": True})


# ---------------------------------------------------------------------------
# Compliance Issues (Ownership + Overdue rule)
# ---------------------------------------------------------------------------

@api.route("/compliance-issues", methods=["GET"])
@login_required
def list_compliance_issues():
    controllers.refresh_overdue_compliance_issues()
    return jsonify(models.query("""
        SELECT ci.*, d.name AS department_name, a.title AS audit_title
        FROM compliance_issue ci
        LEFT JOIN department d ON ci.department_id = d.id
        LEFT JOIN audit a ON ci.audit_id = a.id
        ORDER BY ci.due_date ASC
    """))


@api.route("/compliance-issues", methods=["POST"])
@login_required
def create_compliance_issue():
    data = request.get_json(force=True, silent=True) or {}
    if not data.get("owner") or not data.get("due_date"):
        return jsonify({"error": "Owner and Due Date are required"}), 400
    new_id = controllers.raise_compliance_issue({
        "audit_id": data.get("audit_id"),
        "severity": data.get("severity", "Medium"),
        "description": data.get("description", ""),
        "department_id": data.get("department_id"),
        "owner": data.get("owner"),
        "due_date": data.get("due_date"),
        "status": "Open",
    })
    return jsonify({"success": True, "id": new_id}), 201


@api.route("/compliance-issues/<int:cid>", methods=["PUT"])
@login_required
def update_compliance_issue(cid):
    data = request.get_json(force=True, silent=True) or {}
    fields = {k: v for k, v in data.items()
              if k in ("severity", "description", "owner", "due_date", "status")}
    models.update_row("compliance_issue", cid, fields)
    return jsonify({"success": True})


# ---------------------------------------------------------------------------
# Gamification: Badges owned, Rewards redemption, Leaderboard
# ---------------------------------------------------------------------------

@api.route("/leaderboard", methods=["GET"])
@login_required
def get_leaderboard():
    return jsonify(controllers.leaderboard())


@api.route("/employees/<int:eid>/badges", methods=["GET"])
@login_required
def employee_badges(eid):
    return jsonify(models.query("""
        SELECT eb.*, b.name, b.description, b.icon
        FROM employee_badge eb JOIN badge b ON eb.badge_id = b.id
        WHERE eb.employee_id = ?
    """, (eid,)))


@api.route("/rewards/<int:rid>/redeem", methods=["POST"])
@login_required
def redeem_reward(rid):
    data = request.get_json(force=True, silent=True) or {}
    result, code = controllers.redeem_reward(data.get("employee_id"), rid)
    return jsonify(result), code


@api.route("/reward-redemptions", methods=["GET"])
@login_required
def list_redemptions():
    return jsonify(models.query("""
        SELECT rr.*, e.name AS employee_name, r.name AS reward_name
        FROM reward_redemption rr
        JOIN employee e ON rr.employee_id = e.id
        JOIN reward r ON rr.reward_id = r.id
        ORDER BY rr.date DESC
    """))


# ---------------------------------------------------------------------------
# Notifications
# ---------------------------------------------------------------------------

@api.route("/notifications", methods=["GET"])
@login_required
def list_notifications():
    return jsonify(models.query("SELECT * FROM notification ORDER BY created_at DESC LIMIT 50"))


@api.route("/notifications/<int:nid>/read", methods=["POST"])
@login_required
def mark_notification_read(nid):
    models.update_row("notification", nid, {"is_read": 1})
    return jsonify({"success": True})


@api.route("/notification-settings", methods=["GET"])
@login_required
def get_notification_settings():
    return jsonify(models.table_all("notification_settings", order_by="key"))


@api.route("/notification-settings/<key>", methods=["PUT"])
@login_required
def set_notification_setting(key):
    data = request.get_json(force=True, silent=True) or {}
    enabled = 1 if data.get("enabled") else 0
    existing = models.query("SELECT * FROM notification_settings WHERE key = ?", (key,), one=True)
    if existing:
        models.execute("UPDATE notification_settings SET enabled = ? WHERE key = ?", (enabled, key))
    else:
        models.execute("INSERT INTO notification_settings (key, enabled) VALUES (?, ?)", (key, enabled))
    return jsonify({"success": True})


# ---------------------------------------------------------------------------
# ESG Configuration (Settings toggles + score weighting)
# ---------------------------------------------------------------------------

@api.route("/esg-config", methods=["GET"])
@login_required
def get_esg_config():
    return jsonify(models.table_all("esg_config", order_by="key"))


@api.route("/esg-config/<key>", methods=["PUT"])
@login_required
def set_esg_config(key):
    data = request.get_json(force=True, silent=True) or {}
    controllers.set_config(key, data.get("value"))
    return jsonify({"success": True})


# ---------------------------------------------------------------------------
# Dashboard
# ---------------------------------------------------------------------------

@api.route("/dashboard/summary", methods=["GET"])
@login_required
def dashboard_summary():
    scores = controllers.overall_esg_scores()
    dept_scores = models.query("""
        SELECT ds.*, d.name AS department_name FROM department_score ds
        JOIN department d ON ds.department_id = d.id
        ORDER BY ds.total_score DESC
    """)
    emissions_trend = models.query("""
        SELECT date, SUM(amount_co2) AS total_co2
        FROM carbon_transaction GROUP BY date ORDER BY date
    """)
    recent_activity = models.query("""
        SELECT 'CSR' AS type, e.name || ' completed ''' || ca.name || '''' AS message, ep.completion_date AS date
        FROM employee_participation ep
        JOIN employee e ON ep.employee_id = e.id
        JOIN csr_activity ca ON ep.activity_id = ca.id
        WHERE ep.approval_status = 'Approved'
        ORDER BY ep.completion_date DESC LIMIT 5
    """)
    return jsonify({
        "scores": scores,
        "department_ranking": dept_scores,
        "emissions_trend": emissions_trend,
        "recent_activity": recent_activity,
    })


# ---------------------------------------------------------------------------
# Reports
# ---------------------------------------------------------------------------

@api.route("/ai/insights", methods=["GET"])
@login_required
def get_ai_insights():
    try:
        from reports import generate_ai_anomalies
        insights = generate_ai_anomalies()
        return jsonify({"success": True, "insights": insights})
    except Exception as e:
        return jsonify({"success": False, "error": str(e)}), 500

@api.route("/api/reports/<report_type>", methods=["GET"])
@login_required
def generate_report(report_type):
    import reports as ai_reports
    filters = {
        "department_id": request.args.get("department_id"),
        "date_from": request.args.get("date_from"),
        "date_to": request.args.get("date_to"),
        "employee_id": request.args.get("employee_id"),
        "challenge_id": request.args.get("challenge_id"),
        "esg_category": request.args.get("esg_category"),
    }
    data = ai_reports.build_report(report_type, filters)
    return jsonify(data)
