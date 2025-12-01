# Google Cloud Deployment Guide

This guide walks through deploying the Research In Public stack (FastAPI backend + Next.js frontend) entirely on Google Cloud with Vertex AI integrations.

## Quick Command Summary

Use these copy-paste friendly commands (replace placeholder values in angle brackets):

```bash
# 1. Authenticate + select project
gcloud auth login && gcloud config set project <PROJECT_ID>

# 2. Enable services
gcloud services enable run.googleapis.com artifactregistry.googleapis.com secretmanager.googleapis.com aiplatform.googleapis.com

# 3. Create Artifact Registry (one time)
gcloud artifacts repositories create research-in-public --repository-format=docker --location=<REGION> --description="Containers for Research In Public"

# 4. Grant Cloud Run runtime roles
PROJECT_NUMBER=$(gcloud projects describe <PROJECT_ID> --format="value(projectNumber)"); SA="service-${PROJECT_NUMBER}@serverless-robot-prod.iam.gserviceaccount.com"; \
gcloud projects add-iam-policy-binding <PROJECT_ID> --member="serviceAccount:${SA}" --role="roles/aiplatform.user"; \
gcloud projects add-iam-policy-binding <PROJECT_ID> --member="serviceAccount:${SA}" --role="roles/secretmanager.secretAccessor"; \
gcloud projects add-iam-policy-binding <PROJECT_ID> --member="serviceAccount:${SA}" --role="roles/logging.logWriter"

# 5. Create Gemini secret
echo -n "<GEMINI_KEY>" | gcloud secrets create GEMINI_API_KEY --data-file=-

# 6. Build & deploy backend (run from repo root)
gcloud builds submit --tag <REGION>-docker.pkg.dev/<PROJECT_ID>/research-in-public/backend && \
gcloud run deploy research-in-public-api --image <REGION>-docker.pkg.dev/<PROJECT_ID>/research-in-public/backend --region <REGION> --allow-unauthenticated --set-env-vars LOG_LEVEL=info --update-secrets GEMINI_API_KEY=GEMINI_API_KEY:latest

# 7. Build & deploy frontend (run from repo root)
gcloud builds submit frontend --tag <REGION>-docker.pkg.dev/<PROJECT_ID>/research-in-public/frontend && \
gcloud run deploy research-in-public-web --image <REGION>-docker.pkg.dev/<PROJECT_ID>/research-in-public/frontend --region <REGION> --allow-unauthenticated --set-env-vars NEXT_PUBLIC_API_URL=https://<BACKEND_URL>/v1 --set-env-vars PORT=3000
```

> **Tip:** After the backend deploy, copy the printed `Service URL` (e.g., `https://research-in-public-api-xyz-uc.a.run.app`) and use it for `<BACKEND_URL>` when deploying the frontend.

## 1. Project & API Setup

1. Install the [gcloud CLI](https://cloud.google.com/sdk/docs/install) and authenticate:
   ```bash
   gcloud auth login
   gcloud config set project <PROJECT_ID>
   ```
2. Enable required services:
   ```bash
   gcloud services enable \
     run.googleapis.com \
     artifactregistry.googleapis.com \
     secretmanager.googleapis.com \
     aiplatform.googleapis.com
   ```
3. Grant the Cloud Run runtime service account the roles:
   - `roles/aiplatform.user`
   - `roles/secretmanager.secretAccessor`
   - `roles/logging.logWriter`

   Example:
   ```bash
   PROJECT_NUMBER=$(gcloud projects describe <PROJECT_ID> --format="value(projectNumber)")
   SA=service-${PROJECT_NUMBER}@serverless-robot-prod.iam.gserviceaccount.com
   gcloud projects add-iam-policy-binding <PROJECT_ID> \
     --member="serviceAccount:${SA}" \
     --role="roles/aiplatform.user"
   # repeat for other roles
   ```

4. Store sensitive values (e.g., `GEMINI_API_KEY`, `OPENAI_API_KEY`) in Secret Manager:
   ```bash
   echo -n "<SECRET_VALUE>" | gcloud secrets create GEMINI_API_KEY --data-file=-
   gcloud secrets versions add GEMINI_API_KEY --data-file=<(echo -n "<SECRET_VALUE>")
   ```

## 2. Backend (FastAPI) Deployment

1. Build & push the backend image from repo root:
   ```bash
   gcloud builds submit \
     --tag <REGION>-docker.pkg.dev/<PROJECT_ID>/research-in-public/backend
   ```
2. Deploy to Cloud Run:
   ```bash
   gcloud run deploy research-in-public-api \
     --image <REGION>-docker.pkg.dev/<PROJECT_ID>/research-in-public/backend \
     --region <REGION> \
     --allow-unauthenticated \
     --set-env-vars LOG_LEVEL=info \
     --update-secrets GEMINI_API_KEY=GEMINI_API_KEY:latest
   ```
3. Note the Cloud Run URL (e.g., `https://api-xyz-uc.a.run.app`) for the frontend.

## 3. Frontend (Next.js) Deployment

1. Build & push the frontend image (from `frontend/`):
   ```bash
   gcloud builds submit frontend \
     --tag <REGION>-docker.pkg.dev/<PROJECT_ID>/research-in-public/frontend
   ```
2. Deploy to Cloud Run:
   ```bash
   gcloud run deploy research-in-public-web \
     --image <REGION>-docker.pkg.dev/<PROJECT_ID>/research-in-public/frontend \
     --region <REGION> \
     --allow-unauthenticated \
     --set-env-vars NEXT_PUBLIC_API_URL=https://<API_URL>/v1 \
     --set-env-vars PORT=3000
   ```
3. Optional: map a custom domain via Cloud Run domain mappings.

## 4. Vertex AI Integration

1. Initialize Vertex AI in backend code (see `services/gemini_service.py`):
   ```python
   from vertexai import init as vertex_init
   vertex_init(project=settings.google_cloud_project_id, location=settings.google_cloud_region)
   ```
2. If using Matching Engine, create an index/endpoint via Vertex AI and set env vars:
   - `VERTEX_AI_ME_ENDPOINT_ID`
   - `VERTEX_AI_ME_DEPLOYED_INDEX_ID`
   - `USE_VERTEX_AI=true`

3. Ensure the Cloud Run service account has permission to access these resources.

## 5. Observability & Health

- Health endpoint: `/health` (FastAPI) can be monitored via Load Balancer or Cloud Run health checks.
- Logging: Cloud Run streams stdout/stderr to Cloud Logging automatically. Tail logs per service:
  ```bash
  gcloud run services logs read research-in-public-api --region <REGION> --follow
  gcloud run services logs read research-in-public-web --region <REGION> --follow
  ```
- Monitoring: Use Cloud Monitoring dashboards for request/error latency. Quick metrics:
  ```bash
  gcloud run services describe research-in-public-api --region <REGION> --format="value(status.conditions)"
  ```
- Optional: configure Cloud Build triggers for CI/CD to automatically rebuild/deploy on Git pushes.

## 6. Validation Checklist

1. `curl https://<API_URL>/v1/health` → expect `{"status": "ok"}`.
2. Visit the frontend Cloud Run URL → confirm environment banner and API calls succeed.
3. Run end-to-end interaction (chat, scribe draft, struggle map) from deployed UI while watching Cloud Logging for errors.
4. Verify Struggle Map fetch uses Vertex AI (check `/v1/struggles` response time + logs) if endpoint wired up.
5. Capture `/v1/sessions` + `/v1/sessions/{id}/messages?stream=true` traffic via `curl` or Postman to ensure SSE still works behind Cloud Run.


