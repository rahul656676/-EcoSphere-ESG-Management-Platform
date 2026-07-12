import threading
import time
from controllers import refresh_overdue_compliance_issues

def run_scheduler():
    """Background loop that runs daily tasks."""
    while True:
        try:
            # Check for overdue compliance issues and send notifications
            count = refresh_overdue_compliance_issues()
            if count > 0:
                print(f"[Scheduler] Flagged {count} overdue compliance issues.")
        except Exception as e:
            print(f"[Scheduler] Error running background jobs: {e}")
            
        # Run every 24 hours (86400 seconds)
        time.sleep(86400)

def start_background_jobs():
    """Starts the background scheduler thread."""
    thread = threading.Thread(target=run_scheduler, daemon=True)
    thread.start()
    print("[Scheduler] Background jobs started successfully.")
