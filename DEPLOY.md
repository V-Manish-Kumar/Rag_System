# Deployment Guide

## Deploy to Vercel

1. **Push to GitHub**
   ```bash
   git init
   git add .
   git commit -m "Initial commit"
   git remote add origin YOUR_REPO_URL
   git push -u origin main
   ```

2. **Connect to Vercel**
   - Go to [vercel.com](https://vercel.com)
   - Import your GitHub repository
   - Vercel will auto-detect the configuration from `vercel.json`

3. **Add Environment Variables in Vercel Dashboard**
   - Go to Project Settings → Environment Variables
   - Add:
     - `GOOGLE_API_KEY`
     - `QDRANT_URL`
     - `QDRANT_API_KEY`
     - `JINA_API_KEY`

4. **Deploy**
   - Vercel will automatically deploy
   - Frontend will be at: `your-project.vercel.app`
   - API will be at: `your-project.vercel.app/api/*`

## Update Frontend API URL

After deployment, update the API URL in `frontend/src/components/QueryInterface.jsx` and `frontend/src/components/DocumentInput.jsx`:

```javascript
const API_URL = 'https://your-project.vercel.app/api';
```

## Important Notes

- Vercel has serverless function timeout limits (10s on Hobby plan, 60s on Pro)
- Large document uploads may hit timeout limits
- Consider using streaming responses for better UX
- Free Qdrant Cloud tier has usage limits
