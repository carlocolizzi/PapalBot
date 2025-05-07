#!/bin/bash
# Setup script for the Papal News Monitor bot deployment

# Make sure we have the correct Python version
echo "Python version:"
python --version

# Install dependencies
echo "Installing dependencies..."
pip install -r requirements.txt

# Verify installations
echo "Checking installations..."
pip list | grep beautifulsoup4
pip list | grep bs4
pip list | grep lxml
pip list | grep requests
pip list | grep python-dotenv
pip list | grep pytz

# Create a test .env file if not exists (will be overridden by Render environment variables)
if [ ! -f .env ]; then
    echo "Creating a placeholder .env file..."
    cp env.example .env
fi

echo "Setup complete! Ready to run papal_news_monitor_no_nitter.py" 