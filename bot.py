import hmac, hashlib, smtplib, sys, requests, time, os, io, json
import boto3
from flask import Flask, request, abort
from google import genai
from google.genai import types
from email.message import EmailMessage
from apig_wsgi import make_lambda_handler

# --- UTF-8 Fix for Windows ---
if sys.platform == "win32":
    sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding='utf-8')
    sys.stderr = io.TextIOWrapper(sys.stderr.buffer, encoding='utf-8')

app = Flask(__name__)

# --- AWS SSM SECRET FETCHING ---
def get_secret(parameter_name):
    ssm = boto3.client('ssm', region_name='us-east-1')
    try:
        response = ssm.get_parameter(Name=parameter_name, WithDecryption=True)
        return response['Parameter']['Value']
    except Exception as e:
        print(f"CRITICAL: Failed to fetch {parameter_name}: {e}")
        return None

GEMINI_API_KEY = get_secret("/mentor/gemini_key")
GMAIL_PASS = get_secret("/mentor/gmail_pass")
GMAIL_USER = os.getenv("GMAIL_USER")
WEBHOOK_SECRET = os.getenv("WEBHOOK_SECRET")

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
        print("Email sent successfully!")
    except Exception as e:
        print(f"Email Error: {str(e)}")

def get_gemini_task(prompt):
    try:
        response = client.models.generate_content(
            model="gemini-2.0-flash-lite", 
            contents=prompt,
            config=types.GenerateContentConfig(
                temperature=0.7,
                safety_settings=[{"category": c, "threshold": "BLOCK_NONE"} for c in [
                    "HARM_CATEGORY_HARASSMENT", "HARM_CATEGORY_HATE_SPEECH", 
                    "HARM_CATEGORY_SEXUALLY_EXPLICIT", "HARM_CATEGORY_DANGEROUS_CONTENT"
                ]]
            )
        )
        return response.text if response.text else "AI returned empty response."
    except Exception as e:
        return f"Gemini Error: {str(e)}"

def process_github_event(data, event_type):
    action = data.get('action', '')
    repo = data.get('repository', {}).get('full_name', 'Unknown Repo')
    sender = data.get('sender', {}).get('login', 'Someone')
    commits = data.get('commits', [])
    commit_info = f" with message: '{commits[0]['message']}'" if event_type == 'push' and commits else ""
    
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

    # 1. Get the signature from GitHub
    signature = request.headers.get('X-Hub-Signature-256')
    
    # 2. Get the RAW data (Crucial for HMAC)
    # Using request.get_data() ensures we get the exact bytes GitHub sent
    raw_data = request.get_data()

    if not signature or not WEBHOOK_SECRET:
        print("Error: Missing signature or WEBHOOK_SECRET environment variable")
        abort(403)
        
    # 3. Calculate expected signature
    mac = hmac.new(WEBHOOK_SECRET.encode('utf-8'), msg=raw_data, digestmod=hashlib.sha256)
    expected_signature = 'sha256=' + mac.hexdigest()

    # 4. DEBUG LOGGING (Check CloudWatch for these!)
    print(f"DEBUG: Received Signature: {signature}")
    print(f"DEBUG: Expected Signature: {expected_signature}")

    # 5. Compare
    if not hmac.compare_digest(expected_signature, signature):
        print("Security Error: Signature mismatch!")
        abort(403)

    data = request.get_json()
    event_type = request.headers.get('X-GitHub-Event', 'event')

    process_github_event(data, event_type)
    return "OK", 200

lambda_handler = make_lambda_handler(app)

if __name__ == '__main__':
    app.run(host='0.0.0.0', port=5000)