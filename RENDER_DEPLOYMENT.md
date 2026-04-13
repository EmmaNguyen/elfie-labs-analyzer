# Render Deployment Guide

This guide will help you deploy the Elfie AI Labs Analyzer to Render's free tier.

## Prerequisites

- Render account (free) - [sign up at render.com](https://render.com)
- GitHub account connected to Render
- Repository pushed to GitHub

## Step 1: Push Code to GitHub

If you haven't already, push your code to GitHub:

```bash
git remote add origin https://github.com/YOUR_USERNAME/elfie-labs-analyzer.git
git branch -M main
git push -u origin main
```

## Step 2: Deploy Backend to Render

### Backend Deployment

1. **Create Backend Web Service**
   - Go to [render.com/dashboard](https://render.com/dashboard)
   - Click "New +" → "Web Service"
   - Click "Connect to GitHub"
   - Select `elfie-labs-analyzer` repository
   - Configure settings:
     - **Name**: `elfie-labs-analyzer-backend`
     - **Root Directory**: `backend`
     - **Build Command**: `pip install -r requirements.txt`
     - **Start Command**: `uvicorn main:app --host 0.0.0.0 --port $PORT`

2. **Environment Variables**
   Add these environment variables:
   - `PORT`: `8000`
   - `QWEN_API_KEY`: (Optional - app has fallback data)

3. **Deploy**
   - Click "Create Web Service"
   - Wait for deployment to complete (~2-3 minutes)
   - Copy the backend URL (e.g., `https://elfie-labs-analyzer-backend.onrender.com`)

4. **Test Backend**
   ```bash
   curl https://YOUR_BACKEND_URL.onrender.com/health
   ```
   Expected response:
   ```json
   {
     "status": "healthy",
     "timestamp": "2024-01-15T10:30:00"
   }
   ```

## Step 3: Deploy Frontend to Render

### Frontend Deployment

1. **Create Frontend Web Service**
   - Go to [render.com/dashboard](https://render.com/dashboard)
   - Click "New +" → "Web Service"
   - Select `elfie-labs-analyzer` repository
   - Configure settings:
     - **Name**: `elfie-labs-analyzer-frontend`
     - **Root Directory**: `.` (root)
     - **Build Command**: `npm install && npm run build`
     - **Start Command**: `npm start`
     - **Runtime**: `Node`

2. **Environment Variables**
   Add these environment variables:
   - `NEXT_PUBLIC_API_URL`: `https://YOUR_BACKEND_URL.onrender.com`

3. **Deploy**
   - Click "Create Web Service"
   - Wait for deployment to complete (~3-4 minutes)
   - Copy the frontend URL

## Step 4: Configure Domain (Optional)

### Custom Domain Setup

1. Go to your frontend service settings
2. Click "Domains"
3. Add your custom domain
4. Update DNS records as instructed

## Step 5: Test Complete Application

### End-to-End Testing

1. Visit your frontend URL
2. Upload a test PDF
3. Verify API calls work
4. Check that results display correctly

### API Testing

Test the backend endpoints:

```bash
# Health check
curl https://YOUR_BACKEND_URL.onrender.com/health

# Test PDF analysis (requires actual PDF file)
curl -X POST https://YOUR_BACKEND_URL.onrender.com/analyze-pdf \
  -F "pdf_file=@test.pdf" \
  -F "language=en"
```

## Troubleshooting

### Backend Issues

**Build fails:**
- Check that `requirements.txt` exists in backend directory
- Verify Python version compatibility (Python 3.9+)

**Runtime errors:**
- Check Render logs for error messages
- Verify environment variables are set correctly
- Ensure PORT environment variable is configured

### Frontend Issues

**Build fails:**
- Check that `package.json` exists in root directory
- Verify Node.js version compatibility

**API connection fails:**
- Verify `NEXT_PUBLIC_API_URL` is set correctly
- Check that backend is running and accessible
- Test backend health endpoint

### Common Solutions

1. **Backend not responding:**
   - Check Render logs
   - Verify backend deployment status
   - Ensure backend service is running

2. **CORS errors:**
   - Backend CORS is already configured for localhost:3000
   - For production, update CORS settings in `backend/main.py`

3. **Environment variables not working:**
   - Double-check variable names (case-sensitive)
   - Ensure variables are set in correct service
   - Redeploy after changing variables

## Monitoring

### Render Dashboard

- Monitor service status in Render dashboard
- Check logs for errors
- View metrics (CPU, memory, response times)

### Health Checks

Backend includes health check endpoint:
```
https://YOUR_BACKEND_URL.onrender.com/health
```

## Free Tier Limits

Render free tier includes:
- 750 hours/month of service time
- 512MB RAM
- Shared CPU
- Automatic sleep after inactivity
- 15GB disk space

## Cost Optimization

- Use free tier for development
- Upgrade only when needed for production
- Monitor usage to stay within limits
- Consider auto-sleep settings

## Next Steps

After successful deployment:

1. **Set up custom domain** (optional)
2. **Configure SSL certificates** (automatic on Render)
3. **Set up monitoring alerts**
4. **Configure backup strategy**
5. **Set up CI/CD pipeline**

## Support

- Render documentation: [docs.render.com](https://docs.render.com)
- Backend issues: Check `backend/README.md`
- Frontend issues: Check main `README.md`

## Summary

Once deployed, you'll have:
- **Backend**: FastAPI service on Render free tier
- **Frontend**: Next.js app on Render free tier
- **API Integration**: Frontend connected to backend
- **Health Monitoring**: Both services with health checks
- **Free Hosting**: No cost for development usage

The application will be fully functional and ready for the healthcare hackathon evaluation!
