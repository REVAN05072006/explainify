# Explainify – AI-Powered Topic Explainer

Explainify is a simple Flask-based AI app that generates full educational content using the DeepSeek Chat API. Enter any topic and instantly get a complete lesson, flashcards, quiz questions, and a test.

#Features

Full teaching content with sections

Flashcards (5)

Quiz questions (5)

Test with MCQs and Q&A

Clean UI (index.html)

Flask backend with DeepSeek integration

Easily deployable on Render

#Project Structure

index.html
server.py
requirements.txt
Procfile

The project uses a flat structure (no templates or static folders).

#How It Works

The backend sends a structured prompt to DeepSeek.
DeepSeek returns valid JSON only.
The server extracts and validates the JSON.
The frontend displays the results in a readable format.

#Local Installation

Clone the repository

Install dependencies using: pip install -r requirements.txt

Create a .env file with: DEEPSEEK_API_KEY=your_key

Run locally using: python server.py
The app will run at http://127.0.0.1:5000/

#Render Deployment Setup

Build Command: pip install -r requirements.txt
Start Command: gunicorn server:app

Then add an environment variable on Render:
DEEPSEEK_API_KEY=your_api_key

You can also upload your .env file directly in Render.

#Requirements

Flask 3
Flask-CORS
Requests
python-dotenv
Gunicorn

#API Used

DeepSeek Chat via OpenRouter
Model: deepseek/deepseek-chat

License

Open-source and free to use.
