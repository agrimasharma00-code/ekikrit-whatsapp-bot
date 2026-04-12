# 🚀 Deploy Ekikrit to Vercel

Vercel is a **serverless platform** that deploys Python/FastAPI apps instantly. Free tier includes unlimited deployments!

---

## ⚡ Quick Deploy (5 minutes)

### Step 1: Sign Up (if needed)
Visit: https://vercel.com/signup
- Or sign in with GitHub: https://vercel.com/login

### Step 2: Import Project
1. Click **"Add New"** → **"Project"**
2. Click **"Import Git Repository"**
3. Search for `Ekikrit` (or paste: `https://github.com/amritpaxt/Ekikrit`)
4. Click **"Import"**

### Step 3: Configure Environment
Before deploying, add your Twilio credentials:

1. Go to **"Settings"** → **"Environment Variables"**
2. Add these variables:

| Key | Value |
|-----|-------|
| `TWILIO_SID` | `ACe3b5004516d9fb903959e2106f0d7a0f` |
| `TWILIO_TOKEN` | `b88507f9d28093e2a0864022e07a552d` |
| `TWILIO_WHATSAPP` | `whatsapp:+14155238886` |
| `YOUR_NGROK_URL` | (will be your Vercel URL) |

3. Click **"Save"**

### Step 4: Deploy
Click **"Deploy"** button

✅ **Done!** Your URL will be: `https://ekikrit.vercel.app`

---

## 🔗 Update Twilio Webhook

After deployment:

1. **Copy your Vercel URL** from deployment dashboard (e.g., `https://ekikrit.vercel.app`)

2. Go to **Twilio Console** → **WhatsApp Sandbox Settings**

3. Update **"When a message comes in"** webhook to:
   ```
   https://ekikrit.vercel.app/webhook
   ```

4. Click **"Save"**

---

## 🔄 Update Environment Variable

Go back to Vercel and update `YOUR_NGROK_URL`:

1. **Settings** → **Environment Variables**
2. Edit `YOUR_NGROK_URL` and set it to your Vercel URL:
   ```
   https://ekikrit.vercel.app
   ```
3. Click **"Save"** and **redeploy** (it will auto-redeploy)

---

## 📝 CLI Deploy (Alternative)

If you prefer terminal deployment:

### Install Vercel CLI
```bash
npm install -g vercel
```

### Login
```bash
vercel login
```

### Deploy
```bash
cd c:\Users\Admin\OneDrive\Desktop\ekikrit
vercel
```

### Add Environment Variables
```bash
vercel env add production TWILIO_SID
vercel env add production TWILIO_TOKEN
vercel env add production TWILIO_WHATSAPP
vercel env add production YOUR_NGROK_URL
```

### Redeploy with Variables
```bash
vercel --prod
```

---

## ✅ Verify Deployment

### Test Your Endpoint
```bash
curl https://ekikrit.vercel.app/
```

Should return FastAPI docs or similar response.

### Test WhatsApp Bot
1. Save Twilio WhatsApp number: `+1 (415) 523-8886`
2. Send message: `join`
3. Bot should respond! ✅

### Check Logs
```bash
vercel logs --prod
```

---

## 🎯 Features of Vercel Deployment

| Feature | Benefit |
|---------|---------|
| **Global CDN** | Ultra-fast responses worldwide |
| **Auto-scaling** | Handles traffic spikes automatically |
| **Free tier** | Unlimited deployments, 100GB bandwidth |
| **Git integration** | Auto-deploy on every push to GitHub |
| **Custom domain** | Use your own domain (amritpaxt.com) |
| **Environment variables** | Secure credential management |
| **Monitoring** | Built-in logs and analytics |

---

## 🔄 Auto-Deployment

After linking GitHub:
- Every `git push` to `main` automatically deploys
- No manual deployment needed!

```bash
git add .
git commit -m "Update Ekikrit bot"
git push origin main
# ✅ Vercel auto-deploys!
```

---

## 🎨 Custom Domain (Optional)

1. Go to Vercel **Settings** → **Domains**
2. Click **"Add Domain"**
3. Enter your domain (e.g., `ekikrit.amritpaxt.com`)
4. Follow DNS configuration steps

---

## 🚨 Troubleshooting

### Issue: "502 Bad Gateway"
**Solutions:**
1. Check environment variables are set
2. Look at Vercel logs: `vercel logs --prod`
3. Verify Twilio credentials are correct

### Issue: Bot not responding
**Solutions:**
1. Update Twilio webhook URL to your new Vercel URL
2. Verify `YOUR_NGROK_URL` matches Vercel URL
3. Check logs for errors

### Issue: "Module not found"
**Solution:**
Make sure `requirements.txt` has all dependencies:
```bash
vercel logs --prod
```

---

## 📊 Monitor Your Bot

### View Real-time Logs
```bash
vercel logs --prod --follow
```

### Check Deployment History
1. Go to Vercel Dashboard
2. Click on your project
3. View all deployments in "Deployments" tab

### Set Up Alerts
In Vercel Dashboard → **Settings** → **Notifications**

---

## 💡 Pro Tips

1. **Version your deployments:**
   ```bash
   git tag -a v1.0 -m "First production release"
   git push origin v1.0
   ```

2. **Roll back if needed:**
   - Go to Deployments tab
   - Click on previous deployment
   - Click "Promote to Production"

3. **Add a README badge:**
   ```markdown
   [![Deployed on Vercel](https://vercel.com/button)](https://vercel.com/import/git?repo=amritpaxt/Ekikrit)
   ```

---

## 🎉 You're Live!

**Your bot is now live on:** `https://ekikrit.vercel.app`

**Share with:**
- Add to README
- Update GitHub description
- Share on Twitter/LinkedIn

---

## Support

- **Vercel Docs:** https://vercel.com/docs/concepts/get-started/deploy
- **FastAPI on Vercel:** https://vercel.com/docs/concepts/functions/serverless-functions/runtimes/python
- **Issues:** Check Vercel logs or GitHub

---

**Ready? Deploy now and start helping Indians find government schemes! 🇮🇳**
