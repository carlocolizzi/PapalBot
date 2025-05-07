# Papal News Monitor

A service that continuously scans news websites for mentions of papal candidates and sends Telegram notifications with token addresses when matches are found.

## Features

- Monitors multiple news sources at configurable intervals
- Uses advanced AI-like pattern matching to detect real papal election announcements
- Includes confidence scoring to reduce false positives
- Sends formatted Telegram notifications with article details and token addresses
- Runs continuously as a service on Render
- Deduplicates articles to prevent repeated notifications

## Setup & Deployment

### Prerequisites

1. A Telegram bot token (get one from [@BotFather](https://t.me/botfather))
2. Your Telegram chat ID(s) where notifications should be sent
3. A [Render.com](https://render.com) account

### Environment Variables Setup

The application requires certain environment variables to run properly. You have two options to set them up:

#### Option 1: Using a .env file (for local development)

1. Copy the `env.example` file to a new file named exactly `.env`
2. Edit the `.env` file and fill in your actual values:
   ```
   TELEGRAM_BOT_TOKEN=your_actual_bot_token
   TELEGRAM_CHAT_IDS=your_actual_chat_id1,your_actual_chat_id2
   SCAN_INTERVAL=60
   ```
3. Make sure the `.env` file is in the same directory as `papal_news_monitor.py`

> **Note:** The `.env` file should never be committed to a public repository as it contains sensitive information.

#### Option 2: Setting environment variables on Render (for deployment)

Environment variables are configured automatically when using the `render.yaml` file, but you'll need to provide values for sensitive variables like `TELEGRAM_BOT_TOKEN` and `TELEGRAM_CHAT_IDS` during the deployment process.

### Deployment Instructions

#### Option 1: Automatic Deployment via GitHub

1. Fork this repository to your GitHub account
2. Log in to [Render.com](https://render.com)
3. Go to Dashboard > New > Web Service
4. Connect your GitHub repository
5. Configure the service:
   - Name: `papal-news-monitor` (or any name you prefer)
   - Environment: `Python 3`
   - Build Command: `pip install -r requirements.txt`
   - Start Command: `python papal_news_monitor.py`
6. Add the following environment variables:
   - `TELEGRAM_BOT_TOKEN`: Your Telegram bot token
   - `TELEGRAM_CHAT_IDS`: Comma-separated list of chat IDs
   - `SCAN_INTERVAL`: (Optional) Interval in seconds between scans (default: 60)
7. Click "Create Web Service"

#### Option 2: Using render.yaml

If you've forked this repository, it already includes a `render.yaml` file for easy deployment:

1. Fork this repository
2. Log in to Render
3. Go to Dashboard > Blueprint
4. Select your repository
5. Follow the prompts and add your environment variables when requested

### Local Development

To run the service locally:

1. Clone the repository
2. Create a `.env` file with the following variables:
   ```
   TELEGRAM_BOT_TOKEN=your_bot_token
   TELEGRAM_CHAT_IDS=your_chat_id1,your_chat_id2
   SCAN_INTERVAL=60
   ```
3. Install dependencies: `pip install -r requirements.txt`
4. Run the service: `python papal_news_monitor.py`

## Customization

### Adding or Modifying News Sources

Edit the `SITES` list in `papal_news_monitor.py` to add or remove news sources.

### Updating Keywords

Edit the `KEYWORDS` list in `papal_news_monitor.py` to change what keywords to look for.

### Updating Candidates

The `candidati.json` file contains the list of papal candidates to monitor. Each entry should have a `nome` (first name) and `cognome` (last name) field. To modify the candidates:

1. Edit the `candidati.json` file
2. Add or remove entries as needed
3. Redeploy the service (or it will automatically pick up changes if using auto-deploy)

## Monitoring

The service outputs detailed logs that can be viewed in the Render dashboard. You can check these logs to ensure the service is running correctly and to troubleshoot any issues.

## License

This project is for private use only. All rights reserved. 