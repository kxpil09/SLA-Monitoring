# 🚀 Deploy to Render + Vercel (15 Minutes)

## ✅ **STEP 1: Deploy Backend to Render** (10 min)

### 1. Push Code to GitHub
```bash
cd c:\Users\Kapil\Desktop\sla-monitoring
git add .
git commit -m "Ready for Render deployment"
git push origin main
```

### 2. Create Render Account
1. Go to: https://render.com
2. Sign up with GitHub
3. Authorize Render to access your repositories

### 3. Deploy with Blueprint
1. Click **"New +"** → **"Blueprint"**
2. Connect repository: **kxpil09/SLA-Monitoring**
3. Branch: **main**
4. Render will detect `render.yaml`
5. Click **"Apply"**

### 4. Wait for Deployment (5-10 minutes)
Render will automatically create:
- ✅ PostgreSQL database (free, 90 days)
- ✅ Redis instance (free)
- ✅ API service
- ✅ Celery worker
- ✅ Celery beat scheduler

### 5. Get API URL
After deployment:
1. Go to **Dashboard** → **sla-api**
2. Copy the URL: `https://sla-api-xxxx.onrender.com`

---

## ✅ **STEP 2: Deploy Frontend to Vercel** (5 min)

### 1. Go to Vercel
1. Open: https://vercel.com
2. Sign up with GitHub
3. Click **"Add New"** → **"Project"**

### 2. Import Repository
1. Select: **kxpil09/SLA-Monitoring**
2. Click **"Import"**

### 3. Configure Project
```
Framework Preset: Vite
Root Directory: frontend
Build Command: npm run build
Output Directory: dist
Install Command: npm install
```

### 4. Add Environment Variable
```
Name: VITE_API_URL
Value: https://sla-api-xxxx.onrender.com/api/v1
```
(Use your actual Render API URL from Step 1)

### 5. Deploy
Click **"Deploy"** → Wait 2-3 minutes

### 6. Get Frontend URL
Copy: `https://sla-monitoring-xxxx.vercel.app`

---

## ✅ **STEP 3: Test Everything** (2 min)

### Test Backend
```
https://sla-api-xxxx.onrender.com/health
https://sla-api-xxxx.onrender.com/docs
```

### Test Frontend
```
https://sla-monitoring-xxxx.vercel.app
```

### Add a Service
1. Open frontend
2. Click **"Add Service"**
3. Name: `Google`, URL: `https://google.com`
4. Should see health check within seconds

---

## 🎉 **DONE!**

Your app is live:
- **Frontend**: https://sla-monitoring-xxxx.vercel.app
- **Backend**: https://sla-api-xxxx.onrender.com
- **API Docs**: https://sla-api-xxxx.onrender.com/docs

**Cost**: $0 for 90 days (Render free tier)

---

## 📧 **Optional: Enable Email Alerts**

1. Go to Render Dashboard → **sla-api** → **Environment**
2. Add variables:
   ```
   ENABLE_EMAIL_ALERTS=true
   SMTP_HOST=smtp.gmail.com
   SMTP_PORT=587
   SMTP_USER=your-email@gmail.com
   SMTP_PASSWORD=your-app-password
   ALERT_FROM_EMAIL=alerts@yourdomain.com
   ALERT_TO_EMAILS=admin@example.com
   ```
3. Click **"Save Changes"**
4. Service will auto-redeploy

---

## 🐛 **Troubleshooting**

### Frontend can't reach backend
- Check `VITE_API_URL` in Vercel environment variables
- Verify Render API is running (check logs)

### Backend not starting
- Check Render logs: Dashboard → sla-api → Logs
- Wait for database to be ready (first deploy takes 10 min)

### Celery not running checks
- Check worker logs: Dashboard → sla-worker → Logs
- Verify Redis is running

---

## 💰 **Cost After Free Tier (90 days)**

- PostgreSQL: $7/month
- Redis: Free (25MB)
- API + Workers: Free (750 hours/month)
- Frontend (Vercel): Free forever

**Total**: $7/month after 90 days
