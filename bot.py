import hmac, hashlib, smtplib, sys, requests, threading, time, os, io, json
from flask import Flask, request, abort
from google import genai
from google.genai import types
from email.message import EmailMessage
from dotenv import load_dotenv
from mangum import Mangum  # Required for AWS Lambda
import os
import boto3


load_dotenv()

# --- UTF-8 Fix for Windows ---
if sys.platform == "win32":
    sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding='utf-8')
    sys.stderr = io.TextIOWrapper(sys.stderr.buffer, encoding='utf-8')

# --- CONFIGURATION ---
GEMINI_API_KEY = os.getenv("GEMINI_API_KEY")
GMAIL_USER = os.getenv("GMAIL_USER")
GMAIL_PASS = os.getenv("GMAIL_PASS")
WEBHOOK_SECRET = os.getenv("WEBHOOK_SECRET")
GITHUB_USERNAME = os.getenv("GITHUB_USERNAME")
# Detect environment: AWS Lambda sets 'AWS_LAMBDA_FUNCTION_NAME' automatically
IS_AWS = os.environ.get('AWS_LAMBDA_FUNCTION_NAME') is not None

app = Flask(__name__)
client = genai.Client(api_key=GEMINI_API_KEY)

def get_secret(key_name, ssm_path):
    """
    Returns a secret from local environment variables or AWS SSM.
    """
    # 1. Try to get it from local .env first
    local_val = os.getenv(key_name)
    if local_val:
        return local_val

    # 2. If not found locally, try AWS SSM
    try:
        ssm = boto3.client('ssm', region_name='us-east-1')
        parameter = ssm.get_parameter(Name=ssm_path, WithDecryption=True)
        return parameter['Parameter']['Value']
    except Exception as e:
        print(f"Error fetching secret {ssm_path}: {e}")
        return None

# --- USE THE SECRETS ---
load_dotenv() # Load local .env if it exists

# Move the client initialization BELOW the secret fetching
GEMINI_API_KEY = get_secret("GEMINI_API_KEY", "/mentor/gemini_key")
GMAIL_PASS = get_secret("GMAIL_PASS", "/mentor/gmail_pass")

# NOW initialize the client
client = genai.Client(api_key=GEMINI_API_KEY)

def send_email(subject, body):
    msg = EmailMessage()
    clean_body = str(body or "No content").replace("###", "\n---\n###")
    msg.set_content(clean_body)
    msg['Subject'] = subject
    msg['From'] = GMAIL_USER
    msg['To'] = GMAIL_USER
    try:
        with smtplib.SMTP_SSL('smtp.gmail.com', 465) as smtp:
            smtp.login(GMAIL_USER, GMAIL_PASS)
            smtp.send_message(msg)
    except Exception as e:
        print(f"Email Error: {str(e)}")

def get_gemini_task(prompt):
    config = types.GenerateContentConfig(
        temperature=0.7,
        safety_settings=[{"category": c, "threshold": "BLOCK_NONE"} for c in [
            "HARM_CATEGORY_HARASSMENT", "HARM_CATEGORY_HATE_SPEECH", 
            "HARM_CATEGORY_SEXUALLY_EXPLICIT", "HARM_CATEGORY_DANGEROUS_CONTENT"
        ]]
    )
    for attempt in range(3):
        try:
            response = client.models.generate_content(
                model="gemini-2.0-flash", 
                contents=prompt,
                config=config
            )
            return response.text if response.text else "AI returned empty response."
        except Exception as e:
            if "429" in str(e):
                time.sleep(45) 
            else:
                return f"Gemini Error: {str(e)}"
    return "The Mentor is busy. Check back soon!"

def process_github_event(data, event_type):
    """Core logic to generate task and email."""
    action = data.get('action', '')
    repo = data.get('repository', {}).get('full_name', 'Unknown Repo')
    sender = data.get('sender', {}).get('login', 'Someone')
    
    commit_info = f" with message: '{data['commits'][0]['message']}'" if event_type == 'push' and 'commits' in data else ""
    prompt = (
        f"I am a Fresher DevOps Engineer. A '{action} {event_type}' event just happened in "
        f"the repository '{repo}' by user '{sender}'{commit_info}.\n\n"
        "Give me ONE small, foundational DevOps task (15-20 mins) related to this activity. "
        "Format: ### 🎯 The Mission, ### 🛠️ Steps, ### 📚 Concept to Learn"
    )
    
    task = get_gemini_task(prompt)
    send_email(f"🔔 DevOps Activity: {event_type.capitalize()} on {repo}", task)

@app.route('/', methods=['GET', 'POST'])
def handle_webhook():
    if request.method == 'GET':
        return "DevOps Bot Online!", 200

    # Security Verification
    signature = request.headers.get('X-Hub-Signature-256')
    mac = hmac.new(WEBHOOK_SECRET.encode(), msg=request.data, digestmod=hashlib.sha256)
    if not hmac.compare_digest('sha256=' + mac.hexdigest(), signature or ""):
        abort(403)

    data = request.json
    event_type = request.headers.get('X-GitHub-Event', 'event')

    if IS_AWS:
        # On AWS: Process immediately (Lambda stays alive until this function returns)
        process_github_event(data, event_type)
        return "OK (AWS Processed)", 200
    else:
        # Locally: Use thread to respond to GitHub instantly
        threading.Thread(target=process_github_event, args=(data, event_type)).start()
        return "OK (Local Background)", 200

# AWS Lambda Entry Point
lambda_handler = Mangum(app)

if __name__ == '__main__':
    if len(sys.argv) > 1 and sys.argv[1] == "nudge":
        # Run daily nudge logic (can be triggered by AWS EventBridge)
        pass 
    else:
        print("Starting Local Hub on Port 5000...")
        app.run(host='0.0.0.0', port=5000)