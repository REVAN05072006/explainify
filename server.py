# ============================================================
# Explainify — Complete Rebuilt Backend with New Flow
# ============================================================

import os
import json
import requests
import google.generativeai as genai
from flask import Flask, request, jsonify, send_from_directory, Response
from flask_cors import CORS
from dotenv import load_dotenv

load_dotenv()

app = Flask(__name__, static_folder='.')
CORS(app)

DEEPSEEK_API_KEY = os.getenv("DEEPSEEK_API_KEY", "").strip()
if not DEEPSEEK_API_KEY:
    raise Exception("Missing DEEPSEEK_API_KEY in .env")

GEMINI_API_KEY = os.getenv("GEMINI_API_KEY", "").strip()
if not GEMINI_API_KEY:
    print("Warning: GEMINI_API_KEY not found. Study suggestions will not be available.")

# Configure Gemini AI if key is available
if GEMINI_API_KEY:
    genai.configure(api_key=GEMINI_API_KEY)
    gemini_model = genai.GenerativeModel('gemini-pro')

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
        
        # Add study suggestions if Gemini is configured
        if GEMINI_API_KEY:
            try:
                study_suggestions = generate_study_suggestions(topic)
                result["study_suggestions"] = study_suggestions
            except Exception as e:
                print(f"Failed to generate study suggestions: {e}")
                result["study_suggestions"] = [
                    {"topic": "Related concepts", "description": "Explore concepts closely related to what you just learned"},
                    {"topic": "Advanced topics", "description": "Dive deeper into more advanced aspects"},
                    {"topic": "Practical applications", "description": "Learn how this knowledge is applied in real-world scenarios"}
                ]

        return jsonify(result)

    except Exception as e:
        return jsonify({"error": str(e)}), 500


# -------------------------------------------------------------
# GENERATE STUDY SUGGESTIONS WITH GEMINI AI
# -------------------------------------------------------------
def generate_study_suggestions(topic: str):
    """Generate personalized study suggestions using Gemini AI"""
    prompt = f"""
    Based on the topic "{topic}" that the user just studied, suggest 3-4 closely related topics they should study next.
    
    For each suggestion, provide:
    1. Topic name (short, specific, and relevant)
    2. Brief description explaining why it's a good next step
    
    Format the response as a valid JSON array of objects with this exact structure:
    [
      {{
        "topic": "specific topic name here",
        "description": "brief explanation of why this is a good next topic, maximum 15 words"
      }},
      ...
    ]
    
    Make sure topics are:
    - Directly related to {topic}
    - Logical progression from what was learned
    - Not too advanced or too basic
    - Specific and actionable
    
    Return ONLY the JSON array, no additional text.
    """
    
    try:
        response = gemini_model.generate_content(prompt)
        text = response.text.strip()
        
        # Clean the response
        text = text.replace("```json", "").replace("```", "").strip()
        
        # Find JSON array
        start = text.find('[')
        end = text.rfind(']') + 1
        if start == -1 or end <= 0:
            raise Exception("No JSON array found in response")
        
        json_text = text[start:end].strip()
        suggestions = json.loads(json_text)
        
        # Ensure we have 3-4 suggestions
        if len(suggestions) < 3:
            # Add fallback suggestions if we don't have enough
            fallbacks = [
                {"topic": f"Advanced {topic}", "description": "Deeper exploration of advanced concepts"},
                {"topic": f"{topic} Applications", "description": "Real-world applications and use cases"},
                {"topic": f"Related {topic} Concepts", "description": "Important related concepts and principles"}
            ]
            suggestions = suggestions[:3] + fallbacks[len(suggestions):3]
        
        return suggestions[:4]  # Return max 4 suggestions
        
    except Exception as e:
        print(f"Gemini API Error: {e}")
        # Return default suggestions
        return [
            {"topic": f"Advanced {topic}", "description": "Explore more advanced aspects of this topic"},
            {"topic": f"{topic} in Practice", "description": "Learn practical applications and real-world uses"},
            {"topic": f"Related Concepts to {topic}", "description": "Discover important related topics and principles"}
        ]


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
      "answer": "string"  // Must be EXACT text of one of the options
    }}
  ],
  "test": {{
    "mcq_questions": [
      {{
        "question": "string",
        "options": ["A", "B", "C", "D"],
        "answer": "string",  // Must be EXACT text of one of the options
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
1. teaching_content: Provide a complete lesson with introduction, 3-5 sections, and summary
2. Exactly 5 flashcards
3. Exactly 5 quiz questions
4. test: Provide 5 MCQ questions and 3 Q&A questions
5. All MCQ questions must have exactly 4 options
6. Answers must match EXACTLY one of the options (case-sensitive)
7. No text outside JSON
8. Ensure quiz answers are always present in the options
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

    # Validate quiz answers
    validate_quiz_answers(data["quiz"])
    
    # Validate test answers
    for mcq in data["test"]["mcq_questions"]:
        if mcq["answer"] not in mcq["options"]:
            raise Exception(f"Test MCQ answer '{mcq['answer']}' not found in options")

    return data


def validate_quiz_answers(quiz_questions):
    """Validate that quiz answers match one of the options"""
    for i, question in enumerate(quiz_questions):
        answer = question.get("answer", "").strip()
        options = question.get("options", [])
        
        if not answer:
            raise Exception(f"Quiz question {i+1} has no answer")
        
        if not options or len(options) != 4:
            raise Exception(f"Quiz question {i+1} must have exactly 4 options")
        
        # Check if answer matches any option (case-insensitive for flexibility)
        answer_lower = answer.lower()
        options_lower = [opt.lower() for opt in options]
        
        if answer_lower not in options_lower:
            # Try to find partial matches
            found = False
            for opt in options:
                if answer_lower in opt.lower() or opt.lower() in answer_lower:
                    # Update answer to match the exact option text
                    question["answer"] = opt
                    found = True
                    break
            
            if not found:
                raise Exception(f"Quiz question {i+1} answer '{answer}' doesn't match any option: {options}")


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
