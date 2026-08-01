import os
from dotenv import load_dotenv
from caspian_sdk import CommClient 

from openai import OpenAI

# Load environment variables from .env file
load_dotenv()

# Initialize clients
client = CommClient(api_key=os.getenv("CASPIAN_API_KEY"))
ai = OpenAI(api_key=os.getenv("OPENAI_API_KEY"))

# Connect the Telegram channel using the token from your .env
# Fetch the token
telegram_token = os.getenv("TELEGRAM_BOT_TOKEN")

# Validate it exists to satisfy the type checker
if not telegram_token:
    raise ValueError("TELEGRAM_BOT_TOKEN is not set in the .env file")

# Connect the Telegram channel
client.connect_telegram(bot_token=telegram_token)

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
            model="gpt-3.5-turbo",
            messages=[
                {"role": "system", "content": SYSTEM_PROMPT},
                {"role": "user", "content": user_query}
            ]
        )
        reply = response.choices[0].message.content
        message.reply(reply)
        print(f"[Outbound Reply Sent] {reply}")

    except Exception as e:
        print(f"Error handling message: {e}")
        message.reply("Sorry, I encountered an issue processing your request.")

if __name__ == "__main__":
    print("🚀 Caspian Multi-Channel Agent is listening...")
    client.listen()