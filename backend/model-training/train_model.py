import pandas as pd
import numpy as np
from sklearn.model_selection import train_test_split
from sklearn.ensemble import IsolationForest
from sklearn.preprocessing import StandardScaler
from sklearn.pipeline import Pipeline  # NEW: For auto-scaling in serving
from sklearn.metrics import classification_report, precision_recall_fscore_support
import joblib
import os
from google.cloud import aiplatform
from google.cloud import storage

# Config (v3: Pipeline for scaling)
PROJECT_ID = "bulidng-blog"
LOCATION = "us-central1"
BUCKET_NAME = f"{PROJECT_ID}-data"
MODEL_DISPLAY_NAME = "llm-poisoning-anomaly-detector-v3"
GCS_MODEL_DIR = f"gs://{BUCKET_NAME}/models/anomaly_detector_v3"
LOCAL_MODEL_DIR = "model_artifacts_v3"

# Load & prep (same)
df = pd.read_csv("anomaly_train.csv")
df['timestamp'] = pd.to_datetime(df['timestamp'])
df = df.sort_values('timestamp').reset_index(drop=True)
df['time_diff'] = df['timestamp'].diff().dt.total_seconds().fillna(0)
print(f"Loaded {len(df)} logs for training (v3: Pipeline).")

feature_cols = ['prompt_length', 'time_diff', 'user_freq'] + [f'emb_dim_{i}' for i in range(10)]
X = df[feature_cols].fillna(0)
y = df['is_anomalous']

# Scale & split (local only)
scaler = StandardScaler()
X_scaled = scaler.fit_transform(X)
X_train, X_test, y_train, y_test = train_test_split(X_scaled, y, test_size=0.2, random_state=42, stratify=y)

# Train (same)
model = IsolationForest(contamination=0.21, n_estimators=200, random_state=42, n_jobs=-1)
model.fit(X_train)

# Eval (same)
y_pred_test = model.predict(X_test)
y_pred_test_bin = (y_pred_test == -1).astype(int)
prec, rec, f1, _ = precision_recall_fscore_support(y_test, y_pred_test_bin, average='binary')
print(f"=== LOCAL METRICS ===\nPrecision: {prec:.3f} | Recall: {rec:.3f} | F1: {f1:.3f}")

# NEW: Pipeline for serving (scaler + model)
pipeline = Pipeline([('scaler', scaler), ('iso_forest', model)])

# Save ONLY pipeline as model.joblib (no separate scaler)
os.makedirs(LOCAL_MODEL_DIR, exist_ok=True)
joblib.dump(pipeline, os.path.join(LOCAL_MODEL_DIR, "model.joblib"))

# Upload
def upload_folder_to_gcs(local_path, gcs_path):
    client = storage.Client()
    bucket = client.bucket(BUCKET_NAME)
    for root, _, files in os.walk(local_path):
        for file in files:
            local_file = os.path.join(root, file)
            blob_path = f"models/anomaly_detector_v3/{file}"
            blob = bucket.blob(blob_path)
            blob.upload_from_filename(local_file)
            print(f"Uploaded {file} → gs://{BUCKET_NAME}/{blob_path}")

upload_folder_to_gcs(LOCAL_MODEL_DIR, GCS_MODEL_DIR)

# Register (same image)
aiplatform.init(project=PROJECT_ID, location=LOCATION)
CORRECT_IMAGE_URI = "us-docker.pkg.dev/vertex-ai/prediction/sklearn-cpu.1-5:latest"

uploaded_model = aiplatform.Model.upload(
    display_name=MODEL_DISPLAY_NAME,
    artifact_uri=GCS_MODEL_DIR,
    serving_container_image_uri=CORRECT_IMAGE_URI,
    description="Pipeline-wrapped Isolation Forest for LLM poisoning (auto-scales embeddings + behavioral, v3)",
    labels={"phase": "2", "type": "anomaly", "version": "3"}
)

print(f"\nModel v3 uploaded!")
print(f"Resource name: {uploaded_model.resource_name}")
print(f"Model ID: {uploaded_model.name.split('/')[-1]}")  # Copy for deploy