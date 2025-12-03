# ============================================================
# Explainify — Complete Rebuilt Backend with New Flow
# ============================================================

import os
import json
import requests
from flask import Flask, request, jsonify, send_from_directory, Response
from flask_cors import CORS
from dotenv import load_dotenv

load_dotenv()

app = Flask(__name__, static_folder='.')
CORS(app)

DEEPSEEK_API_KEY = os.getenv("DEEPSEEK_API_KEY", "").strip()
if not DEEPSEEK_API_KEY:
    raise Exception("Missing DEEPSEEK_API_KEY in .env")

DEEPSEEK_URL = "https://openrouter.ai/api/v1/chat/completions"


# -------------------------------------------------------------
# HOME PAGE
# -------------------------------------------------------------
@app.route("/")
def home():
    return send_from_directory(".", "index.html")


# -------------------------------------------------------------
# MAIN API ENDPOINT - Now with comprehensive content
# -------------------------------------------------------------
@app.route("/api/generate", methods=["POST", "OPTIONS"])
def api_generate():
    if request.method == "OPTIONS":
        return Response(status=200)

    try:
        data = request.get_json()
        topic = data.get("topic", "").strip()

        if not topic:
            return jsonify({"error": "Topic required"}), 400

        result = call_deepseek(topic)
        return jsonify(result)

    except Exception as e:
        return jsonify({"error": str(e)}), 500


# -------------------------------------------------------------
# DEEPSEEK CALL - Returns Teaching Content + Flashcards + Quiz + Test
# -------------------------------------------------------------
def call_deepseek(topic: str):
    prompt = f"""
Return ONLY valid JSON. No markdown, no notes, no explanations.

Generate comprehensive learning content for the topic: "{topic}"

Your output MUST follow the EXACT structure:

{{
  "teaching_content": {{
    "title": "string",
    "introduction": "string",
    "sections": [
      {{
        "heading": "string",
        "content": "string"
      }}
    ],
    "summary": "string"
  }},
  "flashcards": [
    {{
      "title": "string",
      "explanation": "string",
      "key_point": "string"
    }}
  ],
  "quiz": [
    {{
      "question": "string",
      "options": ["A", "B", "C", "D"],
      "answer": "string"
    }}
  ],
  "test": {{
    "mcq_questions": [
      {{
        "question": "string",
        "options": ["A", "B", "C", "D"],
        "answer": "string",
        "explanation": "string"
      }}
    ],
    "qa_questions": [
      {{
        "question": "string",
        "answer": "string"
      }}
    ]
  }}
}}

STRICT RULES:
- teaching_content: Provide a complete lesson with introduction, 3-5 sections, and summary
- Exactly 5 flashcards
- Exactly 5 quiz questions (optional quiz)
- test: Provide 5 MCQ questions and 3 Q&A questions (full test)
- All MCQ questions must have exactly 4 options
- Answers must match exactly one of the options
- No text outside JSON
"""

    headers = {
        "Authorization": f"Bearer {DEEPSEEK_API_KEY}",
        "Content-Type": "application/json",
        "HTTP-Referer": "http://localhost",
        "X-Title": "Explainify"
    }

    payload = {
        "model": "deepseek/deepseek-chat",
        "messages": [{"role": "user", "content": prompt}],
        "temperature": 0.4
    }

    res = requests.post(DEEPSEEK_URL, headers=headers, json=payload, timeout=45)

    if res.status_code != 200:
        raise Exception("DeepSeek API Error: " + res.text)

    raw = res.json()
    text = raw["choices"][0]["message"]["content"].strip()

    # Remove accidental code fences
    text = text.replace("```json", "").replace("```", "").strip()

    # Extract JSON block
    start = text.find("{")
    end = text.rfind("}") + 1
    if start == -1 or end <= 0:
        raise Exception("DeepSeek did not return JSON")

    json_text = text[start:end].strip()

    # Parse JSON
    try:
        data = json.loads(json_text)
    except Exception as e:
        raise Exception("Invalid JSON from DeepSeek: " + str(e))

    # Validate presence of sections
    required_fields = ["teaching_content", "flashcards", "quiz", "test"]
    for field in required_fields:
        if field not in data:
            raise Exception(f"DeepSeek JSON missing required field: {field}")

    return data


# -------------------------------------------------------------
# STATIC FILES
# -------------------------------------------------------------
@app.route("/<path:path>")
def static_files(path):
    return send_from_directory(".", path)


# -------------------------------------------------------------
# RUN SERVER
# -------------------------------------------------------------
if __name__ == "__main__":
    print("Explainify Server Running: http://127.0.0.1:5000")
    app.run(host="127.0.0.1", port=5000, debug=False)