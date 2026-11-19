# YouTube API Credentials Setup

To allow the autonomous upload agent to upload clips directly to your YouTube channel without asking permission each time, follow these one-time steps:

### Step 1: Create a Google Cloud Project
1. Go to [Google Cloud Console](https://console.cloud.google.com/).
2. Click **Select a project** (top bar) > **New Project**, name it `ShortsAutomation`, and click **Create**.

### Step 2: Enable the YouTube Data API v3
1. In your project, go to **APIs & Services** > **Library**.
2. Search for `YouTube Data API v3`.
3. Click on it and click **Enable**.

### Step 3: Configure OAuth Consent Screen
1. Go to **APIs & Services** > **OAuth consent screen**.
2. Select **External** and click **Create**.
3. Fill in:
   - **App name**: `ShortsUploader`
   - **User support email**: Your email
   - **Developer contact email**: Your email
4. Click **Save and Continue** through Scopes (or add `.../auth/youtube.upload`).
5. Under **Test Users**, click **+ Add Users** and enter the Gmail address associated with your YouTube Channel.
6. Click **Save and Continue**.

### Step 4: Download OAuth 2.0 Credentials
1. Go to **APIs & Services** > **Credentials**.
2. Click **+ Create Credentials** > **OAuth client ID**.
3. Application type: Select **Desktop App**.
4. Name: `Shorts Desktop Client`.
5. Click **Create**.
6. In the popup, click **Download JSON**.
7. Rename the downloaded file to `client_secret.json` and place it in this folder:
   `e:\Cliping\credentials\client_secret.json`

### Step 5: One-Time Authorization
Run this command once in your terminal:
```powershell
.\.venv\Scripts\python.exe scripts\upload_youtube.py -i final_clips\clip_1.mp4 -t "Test Clip" -p private
```
A browser tab will open prompting you to sign in with your channel's Google Account. Click **Continue** / **Allow**.

Once authorized:
- A `token.json` file is saved in `credentials/`.
- The token refreshes automatically in the background.
- You will **never** have to log in or grant permission again!
