---
description: How to deploy Pintrends to Render.com
---

# Deploying Pintrends to Render.com

Since we've added a `render.yaml` file to your project, the setup process is mostly automated. Follow these steps:

### 1. Sign Up/Log In
Go to [Render.com](https://render.com) and sign up using your **GitHub account**. This makes connecting your repository very easy.

### 2. Create a New Blueprint
- On your Render Dashboard, click the **New +** button in the top right.
- Select **Blueprint** from the dropdown menu.

### 3. Connect Your Repository
- Find your `pintrends` repository in the list and click **Connect**.
- If you don't see it, you may need to click "Configure GitHub App" to give Render permission to access it.

### 4. Configure the Blueprint
Render will automatically read your `render.yaml` file and show you a setup screen:
- **Service Group Name**: You can name it `pintrends-v1`.
- **Environment Variables**: Render will show you a list of variables required by the project. You **must** provide your API keys here:
    - `GEMINI_API_KEY`: Your Google Gemini key.
    - `TOGETHER_API_KEY`: Your Together AI key.
    - `FAL_KEY`: Your Fal AI key.
    - `SECRET_KEY`: (Render can generate this automatically, or you can paste a random string).
    - `ALLOWED_HOSTS`: Set this to `pintrends.onrender.com`.
    - `DATABASE_URL`: If you use Render's database (defined in the blueprint), Render will fill this in for you.

### 5. Deploy
- Click **Apply** at the bottom of the page.
- Render will now start the "Build" process using our `build.sh` script. This will:
    - Install Python libraries.
    - Download the Playwright browser.
    - Prepare your static files and database.

### 6. Verification
- Once the status turns to **"Live"**, click on the link provided (e.g., `https://pintrends.onrender.com`).
- Your Pintrends app should be up and running!

> [!TIP]
> **Playwright Note:** The first deployment might take a few minutes extra because it has to download the Chromium browser for your scrapers. This is normal!
