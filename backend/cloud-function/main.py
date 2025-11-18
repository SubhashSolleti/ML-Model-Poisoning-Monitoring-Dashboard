# main.py — FINAL VERSION WITH MITIGATION
import functions_framework
import json
import datetime
import numpy as np
import re
from datetime import UTC
from google.cloud import aiplatform, firestore
from vertexai.language_models import TextEmbeddingModel
from vertexai.generative_models import GenerativeModel, GenerationConfig

# Init once
aiplatform.init(project="bulidng-blog", location="us-central1")
endpoint = aiplatform.Endpoint("projects/bulidng-blog/locations/us-central1/endpoints/8546731481609797632")
embed_model = TextEmbeddingModel.from_pretrained("gemini-embedding-001")
db = firestore.Client()

MEDIAN_USER_FREQ = 21.0
MEDIAN_TIME_DIFF = 0.0

def get_user_stats(user_id):
    docs = list(db.collection("queries").where("user_id", "==", user_id)
               .order_by("timestamp", "DESCENDING").limit(50).stream())
    user_freq = len(docs) + 1
    time_diff = MEDIAN_TIME_DIFF
    if len(docs) >= 2:
        latest = docs[0].to_dict()['timestamp'].replace("Z", "+00:00")
        prev = docs[1].to_dict()['timestamp'].replace("Z", "+00:00")
        time_diff = (datetime.datetime.fromisoformat(latest) - 
                     datetime.datetime.fromisoformat(prev)).total_seconds()
    return user_freq, time_diff

def generate_embedding(prompt: str):
    return np.array(embed_model.get_embeddings([prompt[:8000]])[0].values)

@functions_framework.cloud_event
def process_new_query(cloud_event):
    data = cloud_event.data
    doc_id = data["name"].split("/")[-1]
    doc = db.collection("queries").document(doc_id).get()
    if not doc.exists: return
    log = doc.to_dict()

    prompt = log.get("prompt", "")
    user_id = log.get("user_id", 999)
    ip_address = log.get("ip_address", "0.0.0.0")

    # Feature build
    prompt_length = len(prompt)
    user_freq, time_diff = get_user_stats(user_id)
    emb_10 = generate_embedding(prompt)[:10]
    features = np.array([[prompt_length, time_diff, user_freq] + emb_10.tolist()])

    # Anomaly detection
    pred = endpoint.predict(instances=features.tolist()).predictions[0]
    is_anomaly = pred == -1

    if not is_anomaly:
        print(f"Normal: {doc_id}")
        return "OK"

    # CLASSIFY + MITIGATE
    model = GenerativeModel("gemini-2.5-pro")
    response = model.generate_content(f"""
    Respond with ONLY valid JSON. No markdown.

    Prompt: {prompt}

    {{
      "risk": "low|medium|high",
      "type": "jailbreak|backdoor|data_leak|other",
      "rationale": "1-2 sentences",
      "recommended_mitigation": "Block IP / Quarantine / Retrain / None",
      "hardened_prompt": "If safe version exists, rewrite the user prompt to be non-malicious. Otherwise: null"
    }}
    """, generation_config=GenerationConfig(temperature=0, max_output_tokens=400))

    raw = response.text.strip().strip("```json").strip("```").strip()
    classification = json.loads(re.search(r'\{.*\}', raw, re.DOTALL).group())

    # AUTO MITIGATION
    mitigation_actions = []
    if classification["risk"] == "high":
        # Block IP (mock Cloud Armor)
        db.collection("blocked_ips").document(ip_address.replace(".", "_")).set({
            "ip": ip_address,
            "reason": classification["type"],
            "blocked_at": datetime.datetime.now(UTC).isoformat() + "Z",
            "expires_at": (datetime.datetime.now(UTC) + datetime.timedelta(hours=24)).isoformat() + "Z"
        })
        mitigation_actions.append("IP_BLOCKED")

    # Store full threat
    threat = {
        "original_log_id": doc_id,
        "prompt": prompt,
        "user_id": user_id,
        "ip_address": ip_address,
        "timestamp": datetime.datetime.now(UTC).isoformat() + "Z",
        "anomaly_score": float(pred),
        "classification": classification,
        "mitigation_actions": mitigation_actions,
        "status": "mitigated" if mitigation_actions else "reviewed"
    }
    db.collection("threats").document(doc_id).set(threat)

    print(f"THREAT MITIGATED → Risk: {classification['risk']} | Actions: {mitigation_actions}")
    return "OK"