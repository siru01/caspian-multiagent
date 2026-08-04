import os
import threading
import json
from http.server import HTTPServer, BaseHTTPRequestHandler
from dotenv import load_dotenv
from caspian_sdk import CommClient 
from openai import OpenAI
from database import log_message, get_analytics

# Load environment variables from .env file
load_dotenv()

# Initialize clients
client = CommClient(api_key=os.getenv("CASPIAN_API_KEY"))

# Point OpenAI client to Gemini using your Gemini API key
ai = OpenAI(
    api_key=os.getenv("GEMINI_API_KEY"),
    base_url="https://generativelanguage.googleapis.com/v1beta/openai/"
)

# Fetch Telegram token
telegram_token = os.getenv("TELEGRAM_BOT_TOKEN")
if not telegram_token:
    raise ValueError("TELEGRAM_BOT_TOKEN is not set in the .env file")

# Connect Telegram channel
client.connect_telegram(bot_token=telegram_token)

# Connect Discord channel
client.install_discord()

SYSTEM_PROMPT = """
You are an intelligent customer onboarding and FAQ assistant powered by the Caspian SDK.
Your job is to answer support questions accurately, concisely, and politely across all connected Caspian messaging channels.
"""

@client.on_message
def handle_message(message):
    user_query = message.text
    print(f"[Inbound Message] {user_query}")

    try:
        response = ai.chat.completions.create(
            model="gemini-3.6-flash",
            messages=[
                {"role": "system", "content": SYSTEM_PROMPT},
                {"role": "user", "content": user_query}
            ]
        )
        reply = response.choices[0].message.content
        message.reply(reply)
        print(f"[Outbound Reply Sent] {reply}")

        # Safely determine channel
        channel = "unknown"
        for attr in ["channel", "platform", "source", "service"]:
            try:
                val = getattr(message, attr, None)
                if val:
                    channel = str(val)
                    break
            except Exception:
                pass
        
        # Log inbound messaging query to analytics
        log_message(user_query, reply, channel=channel)

    except Exception as e:
        print(f"Error handling message: {e}")
        message.reply("Sorry, I encountered an issue processing your request.")

class APIHandler(BaseHTTPRequestHandler):
    def end_headers(self):
        self.send_header('Access-Control-Allow-Origin', '*')
        self.send_header('Access-Control-Allow-Methods', 'GET, POST, OPTIONS')
        self.send_header('Access-Control-Allow-Headers', 'Content-Type')
        super().end_headers()

    def do_OPTIONS(self):
        self.send_response(200)
        self.end_headers()

    def do_GET(self):
        if self.path == '/api/analytics':
            self.send_response(200)
            self.send_header('Content-Type', 'application/json')
            self.end_headers()
            analytics = get_analytics()
            self.wfile.write(json.dumps(analytics).encode('utf-8'))
        else:
            self.send_response(404)
            self.end_headers()
            self.wfile.write(b'{"error": "Not Found"}')

    def do_POST(self):
        if self.path == '/api/chat':
            content_length = int(self.headers.get('Content-Length', 0))
            post_data = self.rfile.read(content_length)
            
            try:
                data = json.loads(post_data.decode('utf-8'))
            except Exception as e:
                self.send_response(400)
                self.send_header('Content-Type', 'application/json')
                self.end_headers()
                self.wfile.write(json.dumps({"error": "Invalid JSON"}).encode('utf-8'))
                return

            query = data.get('query', data.get('message', ''))
            print(f"[API Chat Request] {query}")

            try:
                response = ai.chat.completions.create(
                    model="gemini-3.6-flash",
                    messages=[
                        {"role": "system", "content": SYSTEM_PROMPT},
                        {"role": "user", "content": query}
                    ]
                )
                reply = response.choices[0].message.content
                
                # Log to analytics database
                log_message(query, reply, channel="web_dashboard")
                print(f"[API Chat Reply Sent] {reply}")

                self.send_response(200)
                self.send_header('Content-Type', 'application/json')
                self.end_headers()
                self.wfile.write(json.dumps({"reply": reply}).encode('utf-8'))

            except Exception as e:
                print(f"Error handling API chat: {e}")
                self.send_response(500)
                self.send_header('Content-Type', 'application/json')
                self.end_headers()
                self.wfile.write(json.dumps({"error": str(e)}).encode('utf-8'))
        else:
            self.send_response(404)
            self.end_headers()
            self.wfile.write(b'{"error": "Not Found"}')

def run_api_server():
    server_address = ('127.0.0.1', 8081)
    httpd = HTTPServer(server_address, APIHandler)
    print("📡 HTTP API Server running on http://127.0.0.1:8081...")
    httpd.serve_forever()

if __name__ == "__main__":
    # Start the local API server in a background daemon thread
    api_thread = threading.Thread(target=run_api_server, daemon=True)
    api_thread.start()
    
    print("🚀 Caspian Multi-Channel Agent is listening...")
    client.listen()