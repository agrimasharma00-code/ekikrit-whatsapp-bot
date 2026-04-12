# 🚀 Deployment Guide for Ekikrit

## Option 1: Deploy to Heroku (Recommended)

### Step 1: Install Heroku CLI
- Download from: https://devcenter.heroku.com/articles/heroku-cli

### Step 2: Login to Heroku
```bash
heroku login
```

### Step 3: Create Heroku App
```bash
heroku create your-ekikrit-app
```

### Step 4: Set Environment Variables
```bash
heroku config:set TWILIO_SID=your_account_sid_from_console
heroku config:set TWILIO_TOKEN=your_auth_token_from_console
heroku config:set TWILIO_WHATSAPP=whatsapp:+14155238886
heroku config:set YOUR_NGROK_URL=https://your-ekikrit-app.herokuapp.com
```

### Step 5: Deploy
```bash
git add .
git commit -m "Prepare for production"
git push heroku main
```

### Step 6: Verify Deployment
```bash
heroku open
heroku logs --tail
```

Your app will be live at: `https://your-ekikrit-app.herokuapp.com`

---

## Option 2: Deploy to Railway.app

### Step 1: Sign Up
Visit: https://railway.app

### Step 2: Connect GitHub Repository
1. Click "New Project"
2. Select "Deploy from GitHub repo"
3. Connect your GitHub account
4. Select `amritpaxt/Ekikrit` repository

### Step 3: Add Environment Variables
In Railway dashboard, go to Variables and add:
- `TWILIO_SID`
- `TWILIO_TOKEN`
- `TWILIO_WHATSAPP`
- `YOUR_NGROK_URL`

### Step 4: Deploy
Railway will auto-deploy on every push to `main` branch

Your app URL: `https://your-project.up.railway.app`

---

## Option 3: Deploy to Render

### Step 1: Sign Up
Visit: https://render.com

### Step 2: Create Web Service
1. Click "New +"
2. Select "Web Service"
3. Connect GitHub account
4. Select repository

### Step 3: Configure
- **Name:** ekikrit
- **Environment:** Python 3
- **Build Command:** `pip install -r requirements.txt`
- **Start Command:** `uvicorn main:app --host 0.0.0.0 --port 8000`

### Step 4: Add Environment Variables
Add all Twilio credentials in the dashboard

### Step 5: Deploy
Click "Create Web Service"

---

## Option 4: Deploy to Replit

### Step 1: Create Project
1. Visit: https://replit.com
2. Click "Create Replit"
3. Import from GitHub: `amritpaxt/Ekikrit`

### Step 2: Add Secrets
In Replit's Secrets panel add:
- `TWILIO_SID`
- `TWILIO_TOKEN`
- `TWILIO_WHATSAPP`
- `YOUR_NGROK_URL`

### Step 3: Run
Click "Run" button - Replit generates a live URL

---

## Updating Twilio Webhook

After deployment, update your Twilio WebhookConfiguration:

### In Twilio Console:
1. Go to WhatsApp Sandbox Settings
2. Update "When a message comes in" webhook to:
   ```
   https://your-deployed-app-url/webhook
   ```
3. Save

---

## Monitoring & Logs

### Heroku:
```bash
heroku logs --tail
heroku logs --tail -a your-ekikrit-app
```

### Railway:
Check logs in Railway dashboard → Deployments

### Render:
Check logs in Render dashboard → Logs

---

## Common Issues

### Issue: "ModuleNotFoundError: No module named 'fastapi'"
**Solution:** Make sure `requirements.txt` is in root directory

### Issue: Webhook keeps failing
**Solution:** 
1. Check app logs
2. Verify `YOUR_NGROK_URL` matches deployed URL
3. Test endpoint with: `curl https://your-app-url/webhook`

### Issue: WhatsApp bot not responding
**Solution:**
1. Check webhook URL is correct in Twilio
2. Verify environment variables are set
3. Look at logs for errors

---

## Production Checklist

- [ ] All credentials in environment variables (NOT in code)
- [ ] Webhook URL points to live deployment
- [ ] Requirements.txt has all dependencies
- [ ] Python version specified (runtime.txt)
- [ ] Procfile configured correctly
- [ ] `.gitignore` prevents credential leaks
- [ ] Tested bot on WhatsApp
- [ ] Logs monitored for errors
- [ ] Update README with live URL

---

## Live App URL

After deployment, update your README with the live URL:

```markdown
**Live Demo:** https://your-deployed-app-url/webhook
```

---

## Support

For issues:
1. Check deployment platform logs
2. Verify Twilio webhook configuration
3. Test locally first with ngrok
4. Open GitHub issue with error details

---

**Ready to deploy? Choose one option above and follow the steps!**
