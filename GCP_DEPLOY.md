# GCP Cloud Run Deployment Guide

## Prerequisites
1. Install Google Cloud SDK: https://cloud.google.com/sdk/docs/install
2. Authenticate: `gcloud auth login`
3. Set project: `gcloud config set project YOUR_PROJECT_ID`
4. Enable APIs:
```bash
gcloud services enable run.googleapis.com
gcloud services enable cloudbuild.googleapis.com
```

## Deployment Steps

### 1. Build and Deploy to Cloud Run

From the `backend` directory:

```bash
cd backend

gcloud run deploy mini-rag-backend \
  --source . \
  --platform managed \
  --region us-central1 \
  --allow-unauthenticated \
  --set-env-vars GOOGLE_API_KEY=YOUR_GOOGLE_API_KEY,QDRANT_URL=YOUR_QDRANT_URL,QDRANT_API_KEY=YOUR_QDRANT_API_KEY,JINA_API_KEY=YOUR_JINA_API_KEY \
  --memory 2Gi \
  --cpu 2 \
  --timeout 300 \
  --min-instances 0 \
  --max-instances 10
```

**Or set env vars in Cloud Run Console:**
- Go to Cloud Run > mini-rag-backend > Edit & Deploy New Revision
- Add environment variables:
  - `GOOGLE_API_KEY`
  - `QDRANT_URL`
  - `QDRANT_API_KEY`
  - `JINA_API_KEY`

### 2. Get Your Backend URL

After deployment, you'll get a URL like:
```
https://mini-rag-backend-xxxxx-uc.a.run.app
```

### 3. Update Frontend

Set the environment variable in Vercel:
- Go to Vercel Dashboard > Your Project > Settings > Environment Variables
- Add: `VITE_API_URL` = `https://mini-rag-backend-xxxxx-uc.a.run.app`
- Redeploy frontend

### 4. Test

```bash
# Health check
curl https://mini-rag-backend-xxxxx-uc.a.run.app/health

# Stats
curl https://mini-rag-backend-xxxxx-uc.a.run.app/stats
```

## Configuration

### Memory & CPU
- Default: 1Gi memory, 1 CPU
- Recommended: 2Gi memory, 2 CPU (for better performance)
- Max: 8Gi memory, 4 CPU

### Timeout
- Default: 300s (5 minutes)
- Max: 3600s (1 hour)

### Scaling
- `--min-instances 0`: Scale to zero (free tier friendly)
- `--max-instances 10`: Max concurrent instances

## Cost Estimate (Free Tier)

**GCP Cloud Run Free Tier (per month):**
- 2 million requests
- 360,000 GB-seconds memory
- 180,000 vCPU-seconds
- 1GB egress

**Typical usage for this app:**
- ~500ms per request = 2000 free requests/month on 1GB instance
- Scale to zero when idle = no cost

## Monitoring

View logs:
```bash
gcloud run services logs read mini-rag-backend --region us-central1
```

View metrics:
- Go to Cloud Run Console > mini-rag-backend > Metrics

## Update Deployment

```bash
cd backend
gcloud run deploy mini-rag-backend \
  --source . \
  --region us-central1
```

## Delete Service

```bash
gcloud run services delete mini-rag-backend --region us-central1
```

## Frontend on Vercel

The frontend stays on Vercel (static hosting). Just update the API URL:

1. Vercel Dashboard > Environment Variables
2. Add: `VITE_API_URL` = `https://your-cloud-run-url.run.app`
3. Redeploy

## Architecture

```
User → Vercel (Frontend) → Cloud Run (Backend API) → Qdrant Cloud
                                   ↓
                            Google Gemini API
                                   ↓
                              Jina AI Reranker
```

## Troubleshooting

**Container fails to start:**
- Check logs: `gcloud run services logs read mini-rag-backend`
- Verify environment variables are set

**Port issues:**
- Cloud Run sets PORT env var automatically (default 8080)
- Dockerfile uses `${PORT}` variable

**Memory/Timeout:**
- Increase: `--memory 4Gi --timeout 600`

**Cold starts:**
- Set: `--min-instances 1` (keeps 1 instance warm, costs ~$10/month)
