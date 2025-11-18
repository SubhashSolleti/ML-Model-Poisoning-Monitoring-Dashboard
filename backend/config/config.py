from google.cloud import firestore
from datetime import datetime, UTC

db = firestore.Client(project="bulidng-blog")
config = {
    "model_endpoint": "gemini-2.5-pro",  # Swap for other models as needed
    "quarantine_threshold": "high",
    "hardening_enabled": True,
    "alert_enabled": False, 
    "duration_hours": 24,
    "updated_at": datetime.now(UTC).isoformat()
}
db.collection("configs").document("default").set(config)
print("Configs set! Check Firestore > configs/default.")