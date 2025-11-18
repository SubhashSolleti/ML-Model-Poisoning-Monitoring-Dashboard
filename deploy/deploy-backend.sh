#!/bin/bash
echo "Deploying Cloud Function (with auto-mitigation)..."
gcloud functions deploy llm-poisoning-detector \
  --gen2 \
  --region=us-central1 \
  --runtime=python312 \
  --memory=1Gi \
  --cpu=1 \
  --timeout=120s \
  --trigger-event-filters="type=google.cloud.firestore.document.v1.written" \
  --trigger-event-filters="database=(default)" \
  --trigger-event-filters="namespace=projects/bulidng-blog/databases/(default)" \
  --trigger-event-filters="document=queries/{queryId}" \
  --trigger-location=nam5 \
  --entry-point=process_new_query \
  --source=./backend/cloud-function \
  --allow-unauthenticated \
  --quiet

echo "Backend deployed!"