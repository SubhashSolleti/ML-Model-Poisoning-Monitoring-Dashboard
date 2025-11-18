# ML-Model-Poisoning-Monitoring-Dashboard - MVP

A serverless, real-time monitoring layer for detecting, classifying, and mitigating LLM poisoning attempts using **Vertex AI**, **Gemini 2.5 Pro**, **Cloud Functions Gen2**, **Firestore**, and **Cloud Run**.

This MVP validates the core loop: **ingest → detect → classify → mitigate → visualize**, enabling proactive controls for LLM developers and platform teams.

## Overview

LLM systems are increasingly exposed to adversarial prompts, jailbreak attempts, context poisoning, and data manipulation. Traditional debugging is reactive and often too late.

This MVP implements a **proactive LLM safety layer** that:

- Flags anomalous prompts in real time  
- Classifies threats using Gemini 2.5 Pro  
- Blocks abusive IPs automatically  
- Surfaces live insights via a Cloud Run dashboard  
- Operates entirely serverless with minimal operational overhead  

## Architecture

<img width="866" height="2908" alt="ML Model Poisoning_Arch" src="https://github.com/user-attachments/assets/e4fafed2-f517-4983-b457-dd58266579f9" />

### Key Components

- **Firestore** — real-time ingestion and storage of prompt logs  
- **Gemini Embedding Model** — prompt vectorization  
- **Vertex AI Isolation Forest** — anomaly/outlier detection  
- **Gemini 2.5 Pro** — poisoning classification & mitigation reasoning  
- **Cloud Functions Gen2** — detection + enforcement workflow  
- **Cloud Run** — visualization dashboard  


## Features

- Real-time anomaly detection (<5 seconds)  
- Automated threat labeling (jailbreak, backdoor, data leak, prompt injection)  
- Auto-IP blocking  
- Attack timeline graphs  
- Synthetic attack simulator (Demo Mode)  
- Serverless and scalable  

## Prerequisites

- Google Cloud project with billing enabled  
- IAM permissions for: Vertex AI, Firestore, Eventarc, Cloud Run, Cloud Functions  
- Python **3.12**  
- Node.js **18+**  
- Enabled APIs:
  - `aiplatform.googleapis.com`
  - `firestore.googleapis.com`
  - `eventarc.googleapis.com`
  - `cloudfunctions.googleapis.com`
  - `run.googleapis.com`
  - `storage.googleapis.com`


## More Information
For the complete technical write-up, visit the Medium article:  
[How I Built a Real-Time LLM Poisoning Monitoring Dashboard on Google Cloud](https://medium.com/@solletisubhash24/how-i-built-a-real-time-llm-poisoning-monitoring-dashboard-on-google-cloud-51379f58761e)


