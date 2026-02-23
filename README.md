# 📌 PinTrends

A high-performance Pinterest trend analysis and content automation ecosystem built with Django. PinTrends empowers content creators to discover high-velocity trends, expand keyword strategies with AI, and generate complete, image-rich blog posts and pins in seconds, with full end-to-end automation to Pinterest.

## ✨ Features

### 🔍 Intelligence & Discovery
- **Stealth Trend Scraping**: Deep integration with Pinterest Trends using headless Playwright browsers for background data mining.
- **Advanced Filtering**: Narrow down trends by country, interest, age group, and gender.
- **Predictive Analytics**: Interactive charts showing trend trajectories with confidence bounds.

### 🤖 AI Content Engine
- **Full Blog Generation**: Creates complete blog posts including intro, conclusion, and structured sections using Gemini 2.0 Flash.
- **Multi-Model Image Pipeline**:
    - **Together AI (Qwen)**: Generates highly descriptive, aesthetic-focused image prompts.
    - **Fal AI (FLUX/Nano-Banana)**: High-speed, premium image generation.
- **Keyword Expansion**: Transforms seed keywords into high-intent long-tail clusters.

### 📌 Pinterest Automation
- **Direct Posting**: Fully automated pin creation including image upload, title, description, and link attribution.
- **Smart Scheduling**: Built-in scheduler to drip-feed pins at optimal times without an official API.
- **Board & Tag Management**: Automatic board selection and intelligent tag injection for maximum reach.
- **Session Persistence**: Robust headless session management to avoid frequent logins.

### 🖼️ Image & Storage
- **Hybrid Storage**: Full integration with **Cloudflare R2** for scalable, high-speed image hosting.
- **Pin Image Studio**: Specialized vertical image generation optimized for Pinterest's 2:3 aspect ratio.
- **Batch Export**: Download all assets in optimized ZIP files or sync them directly to your Pinterest boards.

## 🛠️ Tech Stack

- **Backend**: Django 5.1 (Python 3.12)
- **Task Queue**: Django Q2 for background scraping and automation.
- **Scraping**: Playwright (Headless Chromium)
- **AI Core**: 
  - **Content**: Google Gemini 2.0 Flash
  - **Prompts**: Together AI (Qwen-2.5 72B)
  - **Images**: Fal AI (FLUX / Nano-Banana)
- **Frontend**: HTMX (Dynamic SPA feel), Tailwind CSS, Bootstrap Icons
- **Storage**: Cloudflare R2 (S3-compatible API)
- **Data Flow**: `boto3` for storage, `requests` for APIs, `ThreadPoolExecutor` for parallel tasks.

## 📦 Installation

### Prerequisites
- Python 3.12+
- Playwright browsers installed (`playwright install chromium`)
- API Keys: Gemini, Together AI, Fal AI

### Setup

1. **Clone & Environment**
   ```bash
   git clone https://github.com/jaimil-creator/pintrends.git
   cd pintrends
   python -m venv .venv
   .venv\Scripts\activate
   pip install -r requirements.txt
   ```

2. **Environment Configuration**
   Create a `.env` file in the project root:
   ```env
   SECRET_KEY=...
   DEBUG=True
   
   # Storage (Cloudflare R2)
   S3_ACCESS_KEY=...
   S3_SECRET_KEY=...
   CLOUDFLARE_ACCOUNT_ID=...
   R2_BUCKET_NAME=...
   R2_BASE_URL=...
   
   # AI Keys
   GEMINI_API_KEY=...
   TOGETHER_API_KEY=...
   FAL_KEY=...
   
   # Pinterest Automantion
   PINTEREST_EMAIL=...
   PINTEREST_PASSWORD=...
   PINTEREST_BOARD=...
   ```

3. **Initialize Database**
   ```bash
   python manage.py migrate
   ```

4. **Launch**
   ```bash
   python manage.py runserver
   ```

## 🚀 The PinTrends Workflow

1. **Discovery**: Scrape Pinterest for seasonal or breakout trends.
2. **Refinement**: Mine suggestions and expand keywords to build niche-specific clusters.
3. **Generation**: Create high-quality blog posts and Pinterest pins with AI.
4. **Automation**: Schedule pins directly to your boards via the automation dashboard.
5. **Sync**: Images are stored in R2 for global accessibility and reliable posting.

## 🚢 Deployment

PinTrends is optimized for containerized deployment:

- **Docker**: use `docker-compose up --build` for local or VPS deployment.
- **Render.com**: Native support with `render.yaml`.
- **VPS**: Scripts for automated setup and process management (check `/vps-setup`).

## 🤝 Contributing

Contributions are welcome! Please feel free to submit a Pull Request.

## 📝 License

This project is private and proprietary.

---
Made with ❤️ for Pinterest content creators
