# 📌 PinTrends

A high-performance Pinterest trend analysis and content automation ecosystem built with Django. PinTrends empowers content creators to discover high-velocity trends, expand keyword strategies with AI, and generate complete, image-rich blog posts and pins in seconds.

## ✨ Features

### 🔍 Intelligence & Discovery
- **Stealth Trend Scraping**: Deep integration with Pinterest Trends using headless Playwright browsers for background data mining.
- **Advanced Filtering**: Narrow down trends by country, interest, age group, and gender.
- **Predictive Analytics**: Interactive charts showing trend trajectories with confidence bounds to spot "breakout" niches.

### 🤖 AI Content Engine
- **Full Blog Generation**: Creates complete blog posts including intro, conclusion, and structured sections using Gemini 1.5 Pro.
- **Multi-Model Image Pipeline**:
    - **Together AI (Qwen)**: Generates highly descriptive, aesthetic-focused image prompts.
    - **Fal AI (Nano-Banana)**: High-speed, high-quality fashion and lifestyle image generation.
- **Keyword Expansion**: Transforms seed keywords into high-intent long-tail clusters.

### 🖼️ Image Management
- **Pin Image Studio**: Specialized vertical image generation optimized for Pinterest's 2:3 aspect ratio.
- **Custom Image Support**: Upload your own assets or regenerate AI images for specific sections.
- **Batch Export**: Download all blog images in a single optimized ZIP file with one click.

### 📊 Project Workflow
- **Workflow Sidebar**: Real-time progress tracking through the project lifecycle (Trends → Suggestions → Expansion → Content → Blog).
- **Intelligent Resumption**: Smart dashboard allows you to jump back into any project exactly where you left off.

## 🛠️ Tech Stack

- **Backend**: Django 5.1 (Python 3.12)
- **Scraping**: Playwright (Headless Chromium)
- **AI Core**: 
  - **Content**: Google Gemini 1.5 Pro / Flash
  - **Prompts**: Together AI (Qwen-2 72B)
  - **Images**: Fal AI (FLUX / Nano-Banana)
- **Frontend**: HTMX (Dynamic SPA feel), Tailwind CSS, Bootstrap Icons
- **Data Flow**: `requests` with connection pooling, `ThreadPoolExecutor` for parallel image processing.

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
   DATABASE_URL=...
   GEMINI_API_KEY=...
   TOGETHER_API_KEY=...
   FAL_KEY=...
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
2. **Refinement**: Mine suggestions and expand keywords to build a niche-specific clusters.
3. **Generation**: Click one button to generate a complete blog post with AI images.
4. **Export**: Serve the content via JSON API or download the images for manual posting.

## 🤝 Contributing

Contributions are welcome! Please feel free to submit a Pull Request.

## 📝 License

This project is private and proprietary.

---
Made with ❤️ for Pinterest content creators
