# Deployment Guide - PatternTrader Pro

Deploy PatternTrader Pro to the web in minutes!

---

## 🚀 Quick Deploy Options

1. **Render.com** (Recommended - Free tier available)
2. **Heroku** (Easy, paid)
3. **Railway** (Fast, generous free tier)
4. **PythonAnywhere** (Simple, free tier)

---

## Option 1: Render.com (RECOMMENDED)

### Why Render?
- ✅ Free tier (750 hours/month)
- ✅ Auto-deploy from GitHub
- ✅ HTTPS included
- ✅ Custom domains supported

### Steps:

**1. Prepare Repository**

Already done! Files in place:
- `requirements.txt` ✅
- `Procfile` ✅  
- `.gitignore` ✅

**2. Push to GitHub**

```bash
cd "/Users/smac/Vault/AI projektit/S&P 500"

# Initialize git (if not done)
git init

# Add all files
git add .

# Commit
git commit -m "Initial commit - PatternTrader Pro"

# Create GitHub repo (on github.com)
# Then connect it:
git remote add origin https://github.com/YOUR_USERNAME/pattern-trader-pro.git
git branch -M main
git push -u origin main
```

**3. Deploy on Render**

1. Go to [render.com](https://render.com)
2. Sign up / Sign in
3. Click "New +" → "Web Service"
4. Connect GitHub repo: `pattern-trader-pro`
5. Configure:
   - **Name**: `patterntrader-pro`
   - **Region**: Choose closest
   - **Branch**: `main`
   - **Build Command**: `pip install -r requirements.txt`
   - **Start Command**: `gunicorn web_dashboard:app --bind 0.0.0.0:$PORT`
   - **Instance Type**: Free
6. Click "Create Web Service"

**Done!** Live in ~2 minutes at: `https://patterntrader-pro.onrender.com`

---

## Option 2: Heroku

### Steps:

**1. Install Heroku CLI**

```bash
brew install heroku/brew/heroku  # macOS
# or download from heroku.com
```

**2. Login**

```bash
heroku login
```

**3. Create App**

```bash
cd "/Users/smac/Vault/AI projektit/S&P 500"
heroku create patterntrader-pro
```

**4. Deploy**

```bash
git push heroku main
```

**5. Open**

```bash
heroku open
```

**Live at**: `https://patterntrader-pro.herokuapp.com`

---

## Option 3: Railway

### Steps:

**1. Install Railway CLI**

```bash
npm install -g @railway/cli
```

**2. Login & Deploy**

```bash
cd "/Users/smac/Vault/AI projektit/S&P 500"
railway login
railway init
railway up
```

**Done!** Railway gives you URL automatically.

---

## Option 4: PythonAnywhere

### Steps:

1. Go to [pythonanywhere.com](https://www.pythonanywhere.com)
2. Sign up (free tier)
3. Upload files via Web tab
4. Install requirements:
   ```bash
   pip3 install --user -r requirements.txt
   ```
5. Configure WSGI file
6. Reload web app

**Live at**: `https://YOUR_USERNAME.pythonanywhere.com`

---

## 🔧 Environment Variables (Optional)

If you want to configure settings:

**Render.com**:
- Go to "Environment" tab
- Add variables:
  - `PORT` (auto-set)
  - `FLASK_ENV=production`

**Heroku**:
```bash
heroku config:set FLASK_ENV=production
```

---

## 🌐 Custom Domain

### Render.com:

1. Go to Settings → Custom Domains
2. Add: `patterntrader.pro`
3. Update DNS records (shown in Render)
4. Wait for SSL (automatic)

**Cost**: Domain ~$10-15/year

---

## 📊 Monitor Deployment

### Render.com:

- **Logs**: Click "Logs" tab
- **Metrics**: Click "Metrics" tab
- **Status**: Shows if running/crashed

### Heroku:

```bash
heroku logs --tail
```

---

## 🔄 Update Deployment

When you make changes:

**1. Commit changes**
```bash
git add .
git commit -m "Update feature X"
git push origin main
```

**2. Auto-deploy**

Render/Railway/Heroku auto-deploy from GitHub!

---

## 🛑 Stop/Delete Deployment

### Render:
1. Go to Settings
2. Click "Delete Web Service"

### Heroku:
```bash
heroku apps:destroy patterntrader-pro
```

---

## 💡 Pro Tips

1. **Free Tier Limits**:
   - Render: 750 hours/month
   - Heroku: 550 hours/month (requires credit card)
   - Railway: $5 credit/month

2. **Keep Alive**:
   - Free dynos sleep after 30 min inactivity
   - Use uptimerobot.com to ping every 5 min (keeps awake)

3. **Performance**:
   - Use Gunicorn (already configured)
   - Enable caching for API calls
   - Compress static files

4. **Security**:
   - Don't commit API keys
   - Use environment variables
   - Enable HTTPS (automatic on Render)

---

## 📈 Scaling (Paid Plans)

When you outgrow free tier:

**Render**:
- Starter: $7/month (always on)
- Standard: $25/month (more resources)

**Heroku**:
- Hobby: $7/month
- Standard: $25/month

**Railway**:
- Pay as you go ($0.000231/GB-hour)

---

## ✅ Checklist

Before deploying:

- [ ] Push to GitHub
- [ ] `requirements.txt` present
- [ ] `Procfile` configured  
- [ ] Test locally first (`python3 web_dashboard.py`)
- [ ] Remove sensitive data
- [ ] Update README with your info

After deploying:

- [ ] Test live URL
- [ ] Check logs for errors
- [ ] Verify dashboard loads
- [ ] Test API endpoints
- [ ] Set up custom domain (optional)
- [ ] Configure monitoring

---

**Ready to deploy?** Pick a platform and go! 🚀
