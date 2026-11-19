# 🚀 Shorts Studio Cloud Deployment Guide

This guide explains how to deploy **Shorts Studio & Universal Clipper** to **Railway** or **Render** for 24/7 cloud operation without keeping your PC on.

---

## ⚡ Option A: Deploy to Railway (Fastest & Recommended)

Railway offers seamless Docker deployment, continuous GitHub integration, and a free trial tier.

### Step 1: Push your code to GitHub
If you haven't pushed your code to GitHub yet, run:
```bash
git init
git add .
git commit -m "Initial commit for Shorts Studio deployment"
git branch -M main
git remote add origin https://github.com/<YOUR_USERNAME>/<YOUR_REPO_NAME>.git
git push -u origin main
```

### Step 2: Create Railway Project
1. Go to [railway.app](https://railway.app) and sign in with GitHub.
2. Click **+ New Project** -> **Deploy from GitHub repo**.
3. Select your repository.
4. Railway will automatically detect the `Dockerfile` and start the build.

### Step 3: Add YouTube OAuth Credentials
1. In your Railway dashboard, click on your service and open the **Variables** tab.
2. Click **+ New Variable**:
   - **Key**: `YOUTUBE_TOKEN_JSON`
   - **Value**: Paste the exact JSON contents of your local `credentials/token.json`.
3. Click **Add**. Railway will automatically redeploy with your authenticated YouTube account!

### Step 4: Generate Public URL
1. Go to the **Settings** tab of your service.
2. Under **Networking**, click **Generate Domain** (e.g. `shorts-studio.up.railway.app`).
3. Open this URL on your phone or PC: your 3-page Studio and Auto-Pilot are now live 24/7!

---

## 🌐 Option B: Deploy to Render

1. Go to [render.com](https://render.com) and sign in.
2. Click **New +** -> **Web Service**.
3. Connect your GitHub repository.
4. Select **Docker** as the Runtime.
5. In **Environment Variables**:
   - Add `YOUTUBE_TOKEN_JSON` with the contents of `credentials/token.json`.
   - Add `PORT` = `5050`
6. Click **Create Web Service**. Render will build and provide your live `https://<service>.onrender.com` URL.

---

## 🐳 Option C: Run with Docker Locally or on a VPS

To run on your local machine or any Linux server using Docker:
```bash
docker-compose up -d --build
```
Access at: `http://localhost:5050`
