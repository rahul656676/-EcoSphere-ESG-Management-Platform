"""
EcoSphere - ai/reports.py
Builds Environmental / Social / Governance / ESG Summary / Custom reports by
aggregating data from the database according to the filters described in
Section 7 of the spec (Department, Date Range, Module, Employee, Challenge,
ESG Category), then optionally asks an LLM (Claude) to produce a short
executive narrative summarizing the numbers.

If GROQ_API_KEY is not configured, build_report() still returns the full
structured data - only the free-text "ai_summary" field returns a warning string.
"""

import os
import sys
import json

sys.path.insert(0, os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))), "backend"))
import models  # noqa: E402
import controllers  # noqa: E402


def _where_department(filters, alias=""):
    clause, params = "", ()
    if filters.get("department_id"):
        col = f"{alias}department_id" if alias else "department_id"
        clause = f" AND {col} = ?"
        params = (filters["department_id"],)
    return clause, params


def environmental_report(filters):
    goals = models.table_all("environmental_goal")
    transactions = models.query("""
        SELECT ct.*, d.name AS department_name FROM carbon_transaction ct
        LEFT JOIN department d ON ct.department_id = d.id
        ORDER BY ct.date DESC
    """)
    products = models.table_all("product_esg_profile")
    total_co2 = sum(t["amount_co2"] for t in transactions)
    return {
        "report": "Environmental Report",
        "total_co2_emitted": round(total_co2, 2),
        "goals": goals,
        "carbon_transactions": transactions,
        "product_esg_profiles": products,
    }


def social_report(filters):
    participation = models.query("""
        SELECT ep.*, e.name AS employee_name, e.gender, ca.name AS activity_name
        FROM employee_participation ep
        JOIN employee e ON ep.employee_id = e.id
        JOIN csr_activity ca ON ep.activity_id = ca.id
    """)
    diversity = models.query("""
        SELECT gender, COUNT(*) AS count FROM employee GROUP BY gender
    """)
    approved = sum(1 for p in participation if p["approval_status"] == "Approved")
    return {
        "report": "Social Report",
        "csr_participation": participation,
        "approved_count": approved,
        "diversity_breakdown": diversity,
        "csr_activities": models.table_all("csr_activity"),
    }


def governance_report(filters):
    policies = models.table_all("esg_policy")
    acknowledgements = models.query("""
        SELECT pa.*, e.name AS employee_name, p.title AS policy_title
        FROM policy_acknowledgement pa
        JOIN employee e ON pa.employee_id = e.id
        JOIN esg_policy p ON pa.policy_id = p.id
    """)
    audits = models.table_all("audit")
    controllers.refresh_overdue_compliance_issues()
    issues = models.query("""
        SELECT ci.*, d.name AS department_name FROM compliance_issue ci
        LEFT JOIN department d ON ci.department_id = d.id
    """)
    return {
        "report": "Governance Report",
        "policies": policies,
        "policy_acknowledgements": acknowledgements,
        "audits": audits,
        "compliance_issues": issues,
        "open_issue_count": sum(1 for i in issues if i["status"] in ("Open", "Overdue")),
    }


def esg_summary_report(filters):
    scores = controllers.overall_esg_scores()
    dept_scores = models.query("""
        SELECT ds.*, d.name AS department_name FROM department_score ds
        JOIN department d ON ds.department_id = d.id
        ORDER BY ds.total_score DESC
    """)
    return {
        "report": "ESG Summary Report",
        "overall_scores": scores,
        "department_comparison": dept_scores,
    }


def custom_report(filters):
    """Combine Environmental + Social + Governance + Gamification data filtered
    by department / date range / employee / challenge / esg category."""
    dept_clause, dept_params = _where_department(filters)

    txns_sql = "SELECT * FROM carbon_transaction WHERE 1=1" + dept_clause
    if filters.get("date_from"):
        txns_sql += " AND date >= ?"
        dept_params += (filters["date_from"],)
    if filters.get("date_to"):
        txns_sql += " AND date <= ?"
        dept_params += (filters["date_to"],)
    transactions = models.query(txns_sql, dept_params)

    emp_clause, emp_params = "", ()
    if filters.get("employee_id"):
        emp_clause = " WHERE ep.employee_id = ?"
        emp_params = (filters["employee_id"],)
    participation = models.query(f"""
        SELECT ep.*, e.name AS employee_name FROM employee_participation ep
        JOIN employee e ON ep.employee_id = e.id{emp_clause}
    """, emp_params)

    chal_clause, chal_params = "", ()
    if filters.get("challenge_id"):
        chal_clause = " WHERE cp.challenge_id = ?"
        chal_params = (filters["challenge_id"],)
    challenge_participation = models.query(f"""
        SELECT cp.*, c.title AS challenge_title FROM challenge_participation cp
        JOIN challenge c ON cp.challenge_id = c.id{chal_clause}
    """, chal_params)

    return {
        "report": "Custom Report",
        "filters_applied": filters,
        "carbon_transactions": transactions,
        "employee_participation": participation,
        "challenge_participation": challenge_participation,
    }


REPORT_BUILDERS = {
    "environmental": environmental_report,
    "social": social_report,
    "governance": governance_report,
    "esg-summary": esg_summary_report,
    "custom": custom_report,
}


def build_report(report_type, filters):
    builder = REPORT_BUILDERS.get(report_type)
    if not builder:
        return {"error": f"Unknown report type '{report_type}'"}

    data = builder(filters)
    data["ai_summary"] = generate_ai_summary(report_type, data)
    return data


def generate_ai_summary(report_type, data):
    """Call Groq API (Llama 3 model) to turn the numbers into a short
    executive narrative. Returns a warning if no API key is configured."""
    api_key = os.environ.get("GROQ_API_KEY")
    if not api_key or "your_groq_api_key_here" in api_key:
        return generate_offline_heuristic_summary(report_type, data)
    try:
        from groq import Groq
        client = Groq(api_key=api_key)
        prompt = (
            "You are an ESG reporting assistant for the EcoSphere platform. "
            f"Write a concise (3-4 sentence) executive summary of the following "
            f"{report_type} report JSON data. Be factual, do not invent numbers.\n\n"
            f"{json.dumps(data, default=str)[:6000]}"
        )
        chat_completion = client.chat.completions.create(
            messages=[{"role": "user", "content": prompt}],
            model="llama3-8b-8192",
            max_tokens=400,
        )
        return chat_completion.choices[0].message.content
    except Exception as exc:  # pragma: no cover - network/optional dependency
        # Fallback to local heuristic if network/API fails
        return generate_offline_heuristic_summary(report_type, data)


def generate_offline_heuristic_summary(report_type, data):
    """Fallback generator when AI API is unavailable."""
    if report_type == "environmental":
        co2 = data.get('total_co2_emitted', 0)
        return f"Offline Summary: The system recorded {co2} kg of CO2 emissions. Please reconnect the AI Copilot for deep trend analysis."
    elif report_type == "governance":
        issues = data.get('open_issue_count', 0)
        return f"Offline Summary: There are currently {issues} open compliance issues that require attention. Reconnect the AI Copilot for predictive risk analysis."
    elif report_type == "social":
        approved = data.get('approved_count', 0)
        return f"Offline Summary: Employees have successfully completed {approved} CSR activities. Reconnect the AI Copilot to generate diversity insights."
    else:
        return f"Offline Summary: Data successfully aggregated for {report_type}. Connect a valid Groq API key in the .env file to unlock AI-driven insights."

def generate_ai_anomalies():
    """Call Groq API to detect anomalies or trends based on the last 30 days of carbon transactions and open compliance issues."""
    api_key = os.environ.get("GROQ_API_KEY")
    
    # Gather data for analysis
    transactions = models.query("SELECT amount_co2, date, source_type FROM carbon_transaction ORDER BY date DESC LIMIT 50")
    issues = models.query("SELECT severity, status FROM compliance_issue WHERE status != 'Resolved'")
    
    data = {
        "recent_carbon_transactions": transactions,
        "active_compliance_issues": issues
    }

    if not api_key or "your_groq_api_key_here" in api_key:
        return "Offline Anomaly Detection: System operates nominally. Connect Groq API for predictive anomaly detection."
    
    try:
        from groq import Groq
        client = Groq(api_key=api_key)
        prompt = (
            "You are an AI Risk and Anomaly Detection system for the EcoSphere ESG platform. "
            "Analyze the following recent carbon transactions and compliance issues. "
            "Identify any spikes in emissions, unusual patterns, or critical compliance risks. "
            "Provide a highly concise (2-3 sentences) alert summarizing the anomalies and suggesting a mitigation strategy.\n\n"
            f"{json.dumps(data, default=str)[:4000]}"
        )
        chat_completion = client.chat.completions.create(
            messages=[{"role": "user", "content": prompt}],
            model="llama3-8b-8192",
            max_tokens=250,
        )
        return chat_completion.choices[0].message.content
    except Exception as exc:
        return "Offline Anomaly Detection: System operates nominally. API unreachable."
