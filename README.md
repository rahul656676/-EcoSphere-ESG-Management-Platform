# EcoSphere - Enterprise ESG Management Platform

EcoSphere is a scalable platform designed to track, manage, and optimize Environmental, Social, and Governance (ESG) metrics for enterprise workflows.

## 🏆 Hackathon Judging Criteria Check

We have meticulously engineered EcoSphere focusing on scalable architecture and enterprise patterns:

1. **Live AI Integration (with Offline Fallback)**: Integrated with **Groq (Llama 3 8B)** to generate real-time AI summaries and anomaly detections. The AI dynamically reads live JSON metrics from the database. *If the API is unavailable or internet disconnects during the demo, the system gracefully falls back to generating a local offline heuristic summary without crashing.*
2. **Security & Authentication Hardening**: 
    - Passwords are cryptographically hashed using PBKDF2:SHA256.
    - The authentication endpoint features an in-memory **IP-based Rate Limiter** to prevent brute-force attacks.
    - **First-run secure initialization**: The default admin password is auto-generated securely on first boot if not provided in `.env`, and printed to the server logs.
3. **Database Scalability (PostgreSQL Native Support)**: The application seamlessly supports both SQLite and PostgreSQL. By providing a `postgres://` connection string in the `DATABASE_URL` environment variable, the application natively connects via `psycopg2`.
4. **Interactive Frontend**: The Dashboard dynamically fetches data, renders real charts, and the AI Copilot features active integrations with the backend.
5. **Automated Testing & CI**: Included a comprehensive `pytest` suite for the models and auth layers. We also include a `.github/workflows/ci.yml` pipeline that runs on every push.
6. **Containerized Deployment**: Production deployment supported via Gunicorn (`gunicorn.conf.py`) and a `docker-compose.yml` for instant, one-click reproducibility.
7. **Complete Feature Implementation**: The Gamification, Notifications, Compliance Tracking, and ESG Score calculation features are fully implemented in the backend schema and controllers.
8. **Automated Database Seeding**: The project repository strictly excludes the SQLite database file (`.gitignore`). On a fresh clone, the first run will automatically generate the schema and populate realistic demonstration seed data.
9. **Health & Ops Endpoints**: Includes standard Python logging and an `/api/health` endpoint for load balancers.

## 🚀 Quick Start (Docker)

1. Clone the repository:
   ```bash
   git clone https://github.com/rahul656676/EcoSphere-ESG-Management-Platform.git
   cd EcoSphere-ESG-Management-Platform
   ```
2. Copy `.env.example` to `.env` and add your **Groq API Key**:
   ```bash
   cp .env.example .env
   ```
3. Run with Docker Compose:
   ```bash
   docker-compose up --build
   ```
4. Access the platform at: `http://localhost:5000`

## 🛠️ Local Development

1. Create a virtual environment and install dependencies:
   ```bash
   pip install -r requirements.txt
   ```
2. Start the application:
   ```bash
   cd backend
   python app.py
   ```

## 🔐 Default Credentials
- **Username**: admin
- **Password**: *Check your terminal/Docker logs on first run for the securely auto-generated password!*

## 🧪 Testing & Health
```bash
# Run automated tests
pytest tests/ -v

# Check health endpoint
curl http://localhost:5000/api/health
```