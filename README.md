# 📌 PinTrends

A powerful Pinterest trend analysis and content generation tool built with Django. Automatically discover trending keywords, generate optimized article titles and pin descriptions using AI, and export your content strategy.

## ✨ Features

### 🔍 Trend Discovery
- **Pinterest Trends Integration**: Scrape trending keywords by interest, demographic, and location
- **Smart Filtering**: Filter by age groups, gender, and specific interests
- **Keyword Review**: Select and manage trending keywords for your niche

### 🤖 AI Content Generation
- **Article Title Generation**: Create engaging, SEO-optimized article titles
- **Pin Description Writing**: Generate compelling pin descriptions
- **Keyword Expansion**: AI-powered keyword expansion for broader reach
- **Inline Editing**: Edit generated content with beautiful modal popups

### 📊 Project Management
- **Dashboard**: Visual overview of all your projects
- **Project Search**: Quickly find projects by name or niche
- **Progress Tracking**: Track your workflow stage for each project
- **Resume Work**: Intelligent navigation to continue where you left off

### 📤 Export Options
- **CSV Export**: Download your content in spreadsheet format
- **JSON Export**: Export structured data for integrations

## 🛠️ Tech Stack

- **Backend**: Django 5.x
- **Database**: PostgreSQL (Supabase)
- **Frontend**: HTML, JavaScript, Tailwind CSS
- **Icons**: Bootstrap Icons
- **HTMX**: Dynamic content loading
- **AI**: OpenAI GPT integration

## 📦 Installation

### Prerequisites
- Python 3.8+
- PostgreSQL database (or Supabase account)
- OpenAI API key

### Setup

1. **Clone the repository**
   ```bash
   git clone https://github.com/jaimil-creator/pintrends.git
   cd pintrends
   ```

2. **Create virtual environment**
   ```bash
   python -m venv .venv
   .venv\Scripts\activate  # Windows
   source .venv/bin/activate  # Mac/Linux
   ```

3. **Install dependencies**
   ```bash
   pip install -r requirements.txt
   ```

4. **Configure environment variables**
   
   Create a `.env` file in the project root:
   ```env
   DATABASE_URL=your_supabase_connection_string
   OPENAI_API_KEY=your_openai_api_key
   SECRET_KEY=your_django_secret_key
   DEBUG=True
   ```

5. **Run migrations**
   ```bash
   python manage.py migrate
   ```

6. **Start the development server**
   ```bash
   python manage.py runserver
   ```

7. **Access the app**
   
   Navigate to `http://127.0.0.1:8000/`

## 🚀 Usage

### Workflow

1. **Create a Project**
   - Click "New Project" from the dashboard
   - Enter project name and niche

2. **Fetch Trends**
   - Select interests and demographics
   - Click "Scrape Trends" to fetch Pinterest keywords
   - Review and select relevant trends

3. **Get AI Suggestions**
   - Generate keyword variations using AI
   - Review suggestions and select the best ones

4. **Expand Keywords**
   - AI expands your keywords into long-tail variations
   - Select keywords for content generation

5. **Generate Content**
   - Set article and pin counts
   - Click "Generate All Content"
   - Edit any generated content inline

6. **Export**
   - Download as CSV or JSON
   - Use in your content strategy

## 📸 Screenshots

### Dashboard
Clean project overview with search functionality

### Content Generation
AI-powered content creation with inline editing

### Trend Analysis
Visual trend data with demographic filters

## 🔐 Security

- Environment variables for sensitive data
- CSRF protection enabled
- Database credentials stored securely
- `.gitignore` configured to exclude sensitive files

## 🤝 Contributing

Contributions are welcome! Please feel free to submit a Pull Request.

## 📝 License

This project is private and proprietary.

## 👤 Author

**Jaimil**
- GitHub: [@jaimil-creator](https://github.com/jaimil-creator)

## 🙏 Acknowledgments

- Pinterest for trend data
- OpenAI for content generation
- Django community for the amazing framework

---

Made with ❤️ for Pinterest content creators
