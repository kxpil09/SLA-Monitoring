# Render Deployment Guide

## 🚀 Quick Deploy

Your code is already on GitHub: https://github.com/kxpil09/SLA-Monitoring

### Step 1: Update Existing Services

Go to your Render dashboard: https://dashboard.render.com/project/prj-d6fl2p0gjchc73bsgneg

#### For Each Service (API, Worker, Beat):

1. **Click on the service**
2. **Go to "Settings"**
3. **Scroll to "Build & Deploy"**
4. **Click "Manual Deploy" → "Deploy latest commit"**

This will pull the latest code from GitHub with all new features!

---

## 🔧 Environment Variables to Add

Go to each service → **Environment** tab and add:

### Email Alert Variables (Optional but Recommended):
```
ENABLE_EMAIL_ALERTS=true
SMTP_HOST=smtp.gmail.com
SMTP_PORT=587
SMTP_USER=your-email@gmail.com
SMTP_PASSWORD=your-app-password
ALERT_FROM_EMAIL=alerts@yourdomain.com
ALERT_TO_EMAILS=admin@example.com
```

---

## 📊 What's New in This Deployment:

✅ **Dynamic Alert Recipients** - Manage email recipients from UI
✅ **Auto Database Migrations** - Alembic runs on startup
✅ **Alert Management UI** - New "📧 Alerts" button in frontend
✅ **Test Suite** - 19 tests with 76% coverage
✅ **Optimized Codebase** - Removed unnecessary files
✅ **Better Error Handling** - Production-ready code

---

## 🌐 Frontend Deployment

### Option 1: Deploy Frontend on Vercel (Recommended - Free)

1. Go to https://vercel.com
2. **Import Project** → Connect GitHub
3. Select `SLA-Monitoring` repo
4. **Root Directory**: `frontend`
5. **Framework Preset**: Vite
6. **Environment Variables**:
   ```
   VITE_API_URL=https://your-api-url.onrender.com/api/v1
   ```
7. **Deploy!**

Your frontend will be live at: `https://sla-monitor.vercel.app`

### Option 2: Deploy Frontend on Render

1. **New → Static Site**
2. Connect GitHub repo
3. **Root Directory**: `frontend`
4. **Build Command**: `npm install && npm run build`
5. **Publish Directory**: `dist`
6. **Environment Variables**:
   ```
   VITE_API_URL=https://your-api-url.onrender.com/api/v1
   ```

---

## 🔄 Update CORS in Backend

After deploying frontend, update `app/main.py`:

```python
app.add_middleware(
    CORSMiddleware,
    allow_origins=[
        "http://localhost:5173",
        "https://your-frontend-url.vercel.app",  # Add your frontend URL
        "https://your-frontend-url.onrender.com"
    ],
    allow_credentials=True,
    allow_methods=["GET", "POST", "PUT", "DELETE", "OPTIONS"],
    allow_headers=["*"],
)
```

Then redeploy API service.

---

## ✅ Verify Deployment

1. **API Health**: `https://your-api-url.onrender.com/health`
2. **API Docs**: `https://your-api-url.onrender.com/docs`
3. **Frontend**: `https://your-frontend-url.vercel.app`

---

## 📝 Resume Links

Add these to your resume:

```
Live Demo: https://your-frontend-url.vercel.app
API Docs: https://your-api-url.onrender.com/docs
GitHub: https://github.com/kxpil09/SLA-Monitoring
```

---

## 🐛 Troubleshooting

### Database Migration Issues:
```bash
# SSH into Render shell (from service dashboard)
alembic upgrade head
```

### Check Logs:
- Go to service → **Logs** tab
- Look for migration success messages

### Redis Connection:
- Ensure Redis service is running
- Check environment variables are set correctly

---

## 💰 Cost Estimate

- **PostgreSQL**: Free for 90 days, then $7/month
- **Redis**: Free (25MB)
- **API Service**: Free (750 hours/month)
- **Worker**: Free (750 hours/month)
- **Beat**: Free (750 hours/month)
- **Frontend (Vercel)**: Free forever

**Total**: FREE for 90 days, then $7/month

---

## 🎉 You're Done!

Your production-ready SLA Monitor is now live with:
- ✅ Real-time monitoring
- ✅ Email alerts
- ✅ Dynamic recipient management
- ✅ Beautiful UI
- ✅ Auto-scaling
- ✅ Professional deployment

Perfect for your resume! 🚀
