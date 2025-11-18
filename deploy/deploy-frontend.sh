#!/bin/bash
cd frontend
echo "Building React app..."
npm run build

echo "Deploying to Cloud Run..."
gcloud run deploy poisoning-shield-dashboard \
  --source . \
  --region=us-central1 \
  --allow-unauthenticated \
  --port=8080 \
  --quiet

echo "Frontend live! URL above"