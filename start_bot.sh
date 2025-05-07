#!/bin/bash

# Check if Python 3.8 is available
PYTHON38="/Library/Frameworks/Python.framework/Versions/3.8/bin/python3.8"

if [ ! -f "$PYTHON38" ]; then
    echo "Error: Python 3.8 not found at $PYTHON38"
    echo "Please install Python 3.8 or update the path in this script."
    exit 1
fi

# Check if .env file exists
if [ ! -f ".env" ]; then
    echo "Error: .env file not found"
    echo "Please copy env.example to .env and update it with your settings."
    echo "cp env.example .env"
    exit 1
fi

# Check if the chat ID has been set properly
CHAT_ID=$(grep "TELEGRAM_CHAT_IDS" .env | cut -d '=' -f2 | tr -d ' ')
if [ "$CHAT_ID" = "YOUR_ACTUAL_CHAT_ID_HERE" ] || [ "$CHAT_ID" = "" ]; then
    echo "Error: Chat ID not set in .env file"
    echo "Please update the TELEGRAM_CHAT_IDS value in .env with your actual chat ID."
    echo "You can get your chat ID by sending a message to @userinfobot in Telegram."
    exit 1
fi

# Run the test script first
echo "Testing Telegram connection..."
"$PYTHON38" test_telegram.py

# Check if the test was successful
if [ $? -ne 0 ]; then
    echo "Telegram test failed. Please check your bot token and chat ID in the .env file."
    exit 1
fi

echo ""
echo "Starting Papal News Monitor..."
echo "Press Ctrl+C to stop the bot"
echo ""

# Start the main script
"$PYTHON38" papal_news_monitor.py 