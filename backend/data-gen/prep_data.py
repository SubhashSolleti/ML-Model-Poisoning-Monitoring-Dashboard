import pandas as pd
from datetime import datetime
from google.cloud import firestore, storage
from vertexai.language_models import TextEmbeddingModel  # Latest 2025 SDK
import numpy as np
from collections import Counter
import json
from sklearn.preprocessing import LabelEncoder  # For categorical if needed

PROJECT_ID = "bulidng-blog"
LOCATION = "us-central1"
BUCKET_NAME = f"{PROJECT_ID}-data"  # Auto-creates if needed
GCS_PATH = f"gs://{BUCKET_NAME}/anomaly_data.csv"

# Step 1: Export from Firestore
db = firestore.Client()
docs = db.collection("queries").stream()
logs = []
for doc in docs:
    logs.append(doc.to_dict())

df = pd.DataFrame(logs)
print(f"Exported {len(df)} logs from Firestore.")

# Step 2: Basic Features
df['prompt_length'] = df['prompt'].str.len()
df['timestamp'] = pd.to_datetime(df['timestamp'])
df = df.sort_values('timestamp')
df['time_diff'] = df['timestamp'].diff().dt.total_seconds().fillna(0)

# User frequency (dynamic: detects bursty attackers)
user_freq = Counter(df['user_id'])
df['user_freq'] = df['user_id'].map(user_freq)

# Label for eval (not used in training; unsupervised)
df['is_anomalous'] = (df['anomaly_score'] > 0.7).astype(int)  # ~20% positive

print("Basic features added. Shape:", df.shape)

# Step 3: Generate Embeddings (Batch via Gemini 2025 SDK)
model = TextEmbeddingModel.from_pretrained("gemini-embedding-001")  # Latest unified model

def batch_embed(prompts, batch_size=200):
    embeddings = []
    for i in range(0, len(prompts), batch_size):
        batch = prompts[i:i+batch_size]
        response = model.get_embeddings(batch)
        batch_emb = [emb.values for emb in response]
        embeddings.extend(batch_emb)
        print(f"Embedded batch {i//batch_size + 1}/{(len(prompts)-1)//batch_size + 1}")
    return np.array(embeddings)

# Truncate long prompts (max 2048 tokens ~8k chars)
df['prompt_trunc'] = df['prompt'].str[:8000]
emb_array = batch_embed(df['prompt_trunc'].tolist())

# Add first 10 dims as features (full 3072 too high-dim; PCA later if needed)
for i in range(10):
    df[f'emb_dim_{i}'] = emb_array[:, i]

print("Embeddings generated (10 dims sampled).")

# Step 4: Save & Upload to GCS
csv_path = "anomaly_train.csv"
df.to_csv(csv_path, index=False)
print(f"Saved {csv_path} (shape: {df.shape}). Columns: {df.columns.tolist()}")

# GCS Upload (latest storage SDK)
client = storage.Client(project=PROJECT_ID)
bucket = client.bucket(BUCKET_NAME)
if not bucket.exists():
    bucket.create(location=LOCATION)
    print(f"Created bucket {BUCKET_NAME}")

blob = bucket.blob("anomaly_data.csv")
blob.upload_from_filename(csv_path)
print(f"Uploaded to {GCS_PATH}")

# Quick Stats
print("\nDataset Preview:")
print(df[['prompt', 'anomaly_score', 'prompt_length', 'emb_dim_0', 'is_anomalous']].head())
print(f"Anomalous ratio: {df['is_anomalous'].mean():.2%}")