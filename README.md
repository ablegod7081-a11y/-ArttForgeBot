# 🎨 ArttForgeBot

An AI-powered Telegram bot for generating stunning images using OpenAI's DALL-E 3.

[![Deploy on Railway](https://railway.app/button.svg)](https://railway.app/template/your-template-link)

## ✨ Features

- 🖼️ Generate AI images from text prompts
- 📐 Customize image size (Square, Portrait, Landscape)
- ✨ Adjust quality (Standard, HD)
- 🎨 Switch styles (Natural, Vivid)
- ⚡ Rate limiting (30 requests/hour)
- 💾 User-specific preferences
- 📊 Clean, user-friendly interface

## 🚀 Quick Deploy

### Option 1: Deploy to Railway (Recommended)

1. Fork this repository
2. Click the "Deploy on Railway" button above
3. Add environment variables:
   - `TELEGRAM_TOKEN` - Your bot token
   - `OPENAI_API_KEY` - Your OpenAI API key
4. Deploy!

### Option 2: Manual Deployment

```bash
# Clone the repository
git clone https://github.com/yourusername/ArttForgeBot.git
cd ArttForgeBot

# Install dependencies
pip install -r requirements.txt

# Set environment variables
export TELEGRAM_TOKEN=your_bot_token
export OPENAI_API_KEY=your_openai_api_key

# Run the bot
python bot.py
