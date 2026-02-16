---
description: How to deploy Pintrends to your VPS using Docker
---

# Deploying Pintrends to your VPS (198.251.79.138)

We have configured Pintrends to run in an **isolated Docker environment**. This means it won't touch or break your existing Docker containers.

### Prerequisites
Make sure `docker` and `docker-compose` are installed on your VPS.

---

### Step 1: Clone the Repository
On your VPS terminal, navigate to your web folder and clone the project:
```bash
git clone https://github.com/jaimil-creator/pintrends.git
cd pintrends
```

### Step 2: Configure Environment Variables
Create a `.env` file in the root directory:
```bash
nano .env
```
Paste your production settings (replace with your real keys):
```env
SECRET_KEY=generate_a_random_string_here
DEBUG=False
ALLOWED_HOSTS=198.251.79.138,localhost
OPENROUTER_API_KEY=your_key_here
GEMINI_API_KEY=your_key_here
TOGETHER_API_KEY=your_key_here
FAL_KEY=your_key_here
```

### Step 3: Launch with Docker
Run the following command to build and start the Pintrends containers in the background:
```bash
docker-compose up --build -d
```

### Step 4: Access the App
The app is now running on port **8080**. You can access it at:
`http://198.251.79.138:8080`

---

### Why this is safe for your VPS:
- **Port 8080**: We've mapped the app to 8080 so it doesn't conflict with any existing websites on port 80 or 443.
- **Isolated Network**: It uses a dedicated network named `pintrends-network`.
- **Pre-installed Scrapers**: The Docker image automatically installs Playwright and Chromium, so you don't have to install any system libraries on your host VPS.

### Troubleshooting
To view logs or see if the app started correctly:
```bash
docker-compose logs -f web
```
