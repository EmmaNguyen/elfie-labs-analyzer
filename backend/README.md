# Backend Deployment Instructions

## Option 1: Render (Recommended - Free Tier)

### Step 1: Create Render Account
1. Go to [render.com](https://render.com)
2. Sign up for a free account
3. Connect your GitHub account

### Step 2: Deploy via Render Dashboard
1. Click "New +"
2. Select "Web Service"
3. Connect your GitHub repository
4. Select the `elfie-labs-analyzer` repository
5. Configure build settings:
   - **Root Directory**: `backend`
   - **Build Command**: `pip install -r requirements.txt`
   - **Start Command**: `uvicorn main:app --host 0.0.0.0 --port $PORT`
6. Add environment variables:
   - `PORT`: `8000`
   - `QWEN_API_KEY`: Your Qwen API key (optional - app has fallback data)
7. Click "Create Web Service"

### Step 3: Get Your Backend URL
After deployment, Render will provide a URL like:
`https://elfie-labs-analyzer-backend.onrender.com`

## Option 2: Railway (Free Tier Available)

### Step 1: Create Railway Account
1. Go to [railway.app](https://railway.app)
2. Sign up for a free account
3. Connect your GitHub account

### Step 2: Deploy via Railway
1. Click "New Project"
2. Select "Deploy from GitHub repo"
3. Choose `elfie-labs-analyzer` repository
4. Railway will auto-detect the backend directory
5. Configure environment variables
6. Deploy

## Option 3: Vercel Serverless Functions

Convert the FastAPI backend to Vercel serverless functions for free hosting.

## Update Frontend API URL

After deploying the backend, update the frontend environment variable:

```bash
# In .env.local
NEXT_PUBLIC_API_URL=https://your-backend-url.com
```

Then redeploy the frontend:
```bash
vercel --prod
```

## Testing the Backend

Once deployed, test the health endpoint:
```bash
curl https://your-backend-url.com/health
```

Expected response:
```json
{
  "status": "healthy",
  "timestamp": "2024-01-15T10:30:00"
}
```
