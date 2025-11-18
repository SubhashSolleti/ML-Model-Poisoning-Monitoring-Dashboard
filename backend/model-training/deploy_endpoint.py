from google.cloud import aiplatform

PROJECT_ID = "bulidng-blog"
LOCATION = "us-central1"
MODEL_ID = "2276155095752114176"  # From v3 upload
ENDPOINT_DISPLAY_NAME = "llm-poisoning-anomaly-endpoint-v3"
DEPLOYED_MODEL_NAME = "poisoning-detector-v3"

aiplatform.init(project=PROJECT_ID, location=LOCATION)

model = aiplatform.Model(model_name=f"projects/{PROJECT_ID}/locations/{LOCATION}/models/{MODEL_ID}")

endpoint = aiplatform.Endpoint.create(display_name=ENDPOINT_DISPLAY_NAME, project=PROJECT_ID, location=LOCATION)
print(f"Endpoint created: {endpoint.resource_name}")

deployed_model = endpoint.deploy(
    model=model,
    deployed_model_display_name=DEPLOYED_MODEL_NAME,
    machine_type="n1-standard-4",
    min_replica_count=1,
    max_replica_count=3,
    traffic_percentage=100,
)

print(f"Model deployed!")
print(f"Endpoint ID: {endpoint.name.split('/')[-1]}")  # Copy for test