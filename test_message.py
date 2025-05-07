import os
import pytest
from dotenv import load_dotenv
import requests
import logging

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s - %(levelname)s - %(message)s",
    handlers=[logging.StreamHandler()],
)
logger = logging.getLogger(__name__)

# Load environment variables
load_dotenv(dotenv_path=".env")

BOT_TOKEN = os.getenv("TELEGRAM_BOT_TOKEN")
CHAT_IDS = os.getenv("TELEGRAM_CHAT_IDS", "").split(",")

def send_test_message(message):
    """
    Send a test message to Telegram
    """
    if not BOT_TOKEN:
        raise ValueError("TELEGRAM_BOT_TOKEN not found in environment variables")
    
    if not CHAT_IDS or CHAT_IDS[0] == "":
        raise ValueError("TELEGRAM_CHAT_IDS not found in environment variables")

    url = f"https://api.telegram.org/bot{BOT_TOKEN}/sendMessage"
    
    for chat_id in CHAT_IDS:
        try:
            payload = {
                "chat_id": chat_id.strip(),
                "text": message,
                "parse_mode": "HTML"
            }
            response = requests.post(url, json=payload)
            response.raise_for_status()
            logger.info(f"Message sent successfully to chat {chat_id}")
        except Exception as e:
            logger.error(f"Failed to send message to chat {chat_id}: {e}")
            raise

def test_send_simple_message():
    """
    Test sending a simple message
    """
    message = "🔔 Test Message\n\nThis is a test message from the PapalBot test suite."
    send_test_message(message)

def test_send_formatted_message():
    """
    Test sending a formatted message with HTML
    """
    message = (
        "🔔 <b>Test Formatted Message</b>\n\n"
        "This is a test message with <i>HTML formatting</i>.\n"
        "• Point 1\n"
        "• Point 2\n"
        "• Point 3"
    )
    send_test_message(message)

if __name__ == "__main__":
    # Run tests
    test_send_simple_message()
    test_send_formatted_message() 