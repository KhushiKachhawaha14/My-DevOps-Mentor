# 🤖 My-DevOps-Mentor

**An AI-powered, event-driven mentorship bot that turns GitHub activity into actionable learning missions.**

---

## 🌟 The "Why"

As a fresher DevOps Engineer, I wanted to bridge the gap between "committing code" and "managing infrastructure." This bot acts as a real-time mentor: it monitors my repository, analyzes my actions using AI, and emails me a 15-minute challenge to improve the project's DevOps maturity.

## 🛠️ Tech Stack

- **Backend:** Python & Flask (Web Server)
- **AI Engine:** Google Gemini 2.0 Flash
- **Infrastructure:** ngrok (Static Domain Tunneling)
- **Secret Management:** Python-Dotenv
- **Security:** HMAC-SHA256 Webhook Signature Verification

## ⚡ Engineering Challenges & Solutions

### 1. Handling Webhook Timeouts

**Problem:** GitHub expects a response within 10 seconds, but AI processing and email delivery often took longer, especially during API rate limits.
**Solution:** Implemented **Asynchronous Processing** using Python `threading`. The server now sends an immediate `200 OK` to GitHub while the background thread handles the "heavy lifting."

### 2. API Resilience

**Problem:** The Gemini API Free Tier frequently hit `429 RESOURCE_EXHAUSTED` errors.
**Solution:** Developed a **Retry Loop** with exponential backoff. The bot intelligently waits for the quota window to reset without failing the mission delivery.

### 3. "Security First" Architecture

**Problem:** Hardcoding credentials creates a massive security vulnerability.
**Solution:** Managed all sensitive data via environment variables (`.env`) and secured the webhook endpoint using cryptographic signature validation.

## 🚀 How to Run Locally

1. **Clone the repo:** `git clone https://github.com/KhushiKachhawaha14/My-DevOps-Mentor.git`
2. **Install Dependencies:** `pip install -r requirements.txt`
3. **Configure Secrets:** Create a `.env` file with your Gemini API Key and Gmail App Password.
4. **Start the Server:** `python bot.py`
5. **Tunnel via ngrok:** `ngrok http --url=your-static-domain 5000`

---

## 📬 Future Roadmap

- [ ] Migrate from local host to **AWS Lambda (Serverless)** for cost-optimization.
- [ ] Use **AWS API Gateway** to manage secure webhook endpoints.
- [ ] Store mission history in **AWS DynamoDB** (NoSQL database).
- [ ] Implement a **CI/CD pipeline** via GitHub Actions to auto-deploy to Lambda.
