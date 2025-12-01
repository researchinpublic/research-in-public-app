#!/bin/bash
set -e

PROJECT_ID="${PROJECT_ID:-$(gcloud config get-value project)}"
REGION="${REGION:-northamerica-northeast1}"

echo "🚀 Deploying Research In Public to GCP"
echo "Project: ${PROJECT_ID}"
echo "Region: ${REGION}"
echo ""

# Verify project is set
if [ -z "$PROJECT_ID" ]; then
    echo "❌ Error: PROJECT_ID not set. Run: gcloud config set project <PROJECT_ID>"
    exit 1
fi

# Check if services are enabled
echo "📋 Checking required services..."
gcloud services enable \
  run.googleapis.com \
  artifactregistry.googleapis.com \
  secretmanager.googleapis.com \
  --project=${PROJECT_ID} 2>/dev/null || true

# Ensure Artifact Registry exists
echo "📦 Checking Artifact Registry..."
gcloud artifacts repositories describe research-in-public \
  --location=${REGION} \
  --project=${PROJECT_ID} 2>/dev/null || \
gcloud artifacts repositories create research-in-public \
  --repository-format=docker \
  --location=${REGION} \
  --description="Containers for Research In Public" \
  --project=${PROJECT_ID}

# Grant Cloud Run service account permissions
echo "🔐 Setting up IAM permissions..."
PROJECT_NUMBER=$(gcloud projects describe ${PROJECT_ID} --format="value(projectNumber)")
# Cloud Run uses the Compute Engine default service account
COMPUTE_SA="${PROJECT_NUMBER}-compute@developer.gserviceaccount.com"

echo "   Granting permissions to: ${COMPUTE_SA}"

gcloud projects add-iam-policy-binding ${PROJECT_ID} \
  --member="serviceAccount:${COMPUTE_SA}" \
  --role="roles/secretmanager.secretAccessor" \
  --condition=None 2>/dev/null || true

gcloud projects add-iam-policy-binding ${PROJECT_ID} \
  --member="serviceAccount:${COMPUTE_SA}" \
  --role="roles/logging.logWriter" \
  --condition=None 2>/dev/null || true

# Enable Cloud Run Invoker role for service-to-service calls
gcloud projects add-iam-policy-binding ${PROJECT_ID} \
  --member="serviceAccount:${COMPUTE_SA}" \
  --role="roles/run.invoker" \
  --condition=None 2>/dev/null || true

# Verify GEMINI_API_KEY secret exists
echo "🔑 Checking GEMINI_API_KEY secret..."
if ! gcloud secrets describe GEMINI_API_KEY --project=${PROJECT_ID} &>/dev/null; then
    echo "⚠️  GEMINI_API_KEY secret not found. Please create it:"
    echo "   printf '%s' '<YOUR_KEY>' | gcloud secrets create GEMINI_API_KEY --data-file=- --project=${PROJECT_ID}"
    read -p "Continue anyway? (y/n) " -n 1 -r
    echo
    if [[ ! $REPLY =~ ^[Yy]$ ]]; then
        exit 1
    fi
fi

# Build and deploy BACKEND
echo ""
echo "🔨 Building backend image..."
gcloud builds submit \
  --tag ${REGION}-docker.pkg.dev/${PROJECT_ID}/research-in-public/backend \
  --project=${PROJECT_ID} \
  --region=${REGION}

echo "🚀 Deploying backend to Cloud Run..."
gcloud run deploy research-in-public-api \
  --image ${REGION}-docker.pkg.dev/${PROJECT_ID}/research-in-public/backend \
  --region ${REGION} \
  --platform managed \
  --allow-unauthenticated \
  --memory 2Gi \
  --cpu 2 \
  --timeout 300 \
  --max-instances 10 \
  --min-instances 0 \
  --set-env-vars LOG_LEVEL=info,USE_LOCAL_VECTOR_STORE=true,USE_VERTEX_AI=false,ENVIRONMENT=production \
  --update-secrets GEMINI_API_KEY=GEMINI_API_KEY:latest \
  --port 8080 \
  --cpu-boost \
  --project=${PROJECT_ID}

# Get backend URLs (both public and internal)
BACKEND_URL=$(gcloud run services describe research-in-public-api \
  --region ${REGION} \
  --format="value(status.url)" \
  --project=${PROJECT_ID})

# Construct internal URL for service-to-service communication
# Format: https://SERVICE-PROJECT_NUMBER-REGION.a.run.app
BACKEND_SERVICE_NAME="research-in-public-api"
# Convert region to short form if needed (e.g., northamerica-northeast1 -> ne1)
REGION_SHORT=$(echo ${REGION} | sed 's/northamerica-northeast1/ne1/; s/us-central1/uc1/; s/us-east1/ue1/; s/us-west1/uw1/; s/europe-west1/ew1/; s/asia-east1/ae1/')
BACKEND_INTERNAL_URL="https://${BACKEND_SERVICE_NAME}-${PROJECT_NUMBER}-${REGION_SHORT}.a.run.app"

echo "✅ Backend deployed: ${BACKEND_URL}"
echo "   Internal URL: ${BACKEND_INTERNAL_URL}"


# Build and deploy FRONTEND
echo ""
echo "🔨 Building frontend image with build-time environment variables..."
cd frontend
gcloud builds submit \
  --config cloudbuild.yaml \
  --substitutions=_NEXT_PUBLIC_API_URL=${BACKEND_URL},_BACKEND_INTERNAL_URL=${BACKEND_INTERNAL_URL},_ENVIRONMENT=production,_REGION=${REGION} \
  --project=${PROJECT_ID} \
  .
cd ..

echo "🚀 Deploying frontend to Cloud Run..."
gcloud run deploy research-in-public-web \
  --image ${REGION}-docker.pkg.dev/${PROJECT_ID}/research-in-public/frontend \
  --region ${REGION} \
  --platform managed \
  --allow-unauthenticated \
  --memory 1Gi \
  --timeout 300 \
  --max-instances 10 \
  --min-instances 0 \
  --port 3000 \
  --project=${PROJECT_ID}

# Grant frontend service account permission to invoke backend (for service-to-service)
FRONTEND_SA=$(gcloud run services describe research-in-public-web \
  --region ${REGION} \
  --format="value(spec.template.spec.serviceAccountName)" \
  --project=${PROJECT_ID})

# If no custom SA, use default compute SA
if [ -z "$FRONTEND_SA" ]; then
  FRONTEND_SA="${PROJECT_NUMBER}-compute@developer.gserviceaccount.com"
fi

echo "🔐 Granting frontend service account permission to invoke backend..."
gcloud run services add-iam-policy-binding research-in-public-api \
  --region ${REGION} \
  --member="serviceAccount:${FRONTEND_SA}" \
  --role="roles/run.invoker" \
  --project=${PROJECT_ID} 2>/dev/null || echo "   (Permission may already exist)"

# Get frontend URL
FRONTEND_URL=$(gcloud run services describe research-in-public-web \
  --region ${REGION} \
  --format="value(status.url)" \
  --project=${PROJECT_ID})

# Update backend with FRONTEND_URL for CORS
echo ""
echo "🔧 Updating backend CORS configuration..."
gcloud run services update research-in-public-api \
  --region ${REGION} \
  --update-env-vars FRONTEND_URL=${FRONTEND_URL} \
  --project=${PROJECT_ID}

echo ""
echo "✅ Deployment complete!"
echo ""
echo "📊 Service URLs:"
echo "   Backend (Public):  ${BACKEND_URL}"
echo "   Backend (Internal): ${BACKEND_INTERNAL_URL}"
echo "   Frontend: ${FRONTEND_URL}"
echo ""
echo "🔐 Service-to-Service:"
echo "   Frontend can call backend using internal URL for better performance"
echo "   Service account: ${FRONTEND_SA}"
echo ""
echo "🧪 Test backend health:"
echo "   curl ${BACKEND_URL}/health"
echo ""
echo "📝 View logs:"
echo "   Backend:  gcloud run services logs read research-in-public-api --region ${REGION} --follow"
echo "   Frontend: gcloud run services logs read research-in-public-web --region ${REGION} --follow"

