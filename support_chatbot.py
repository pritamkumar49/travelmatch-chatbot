import os
import re
from flask import Flask, render_template, request, jsonify
from dotenv import load_dotenv
import google.generativeai as genai
from pathlib import Path

# Load environment variables
load_dotenv()
api_key = os.getenv("GEMINI_API_KEY")

# Configure Gemini
genai.configure(api_key=api_key)

model = genai.GenerativeModel("gemini-3-flash-preview")

# Initialize Flask
app = Flask(__name__, template_folder=str(Path(__file__).parent / 'templates'))

# Simple memory for user sessions
conversation_memory = {}

# -----------------------------
# INTENT DETECTION
# -----------------------------
def detect_intent(message):

    message = message.lower()

    if any(word in message for word in ["travel partner", "companion", "travel with", "find partner"]):
        return "matchmaking"

    if any(word in message for word in ["plan trip", "itinerary", "places to visit", "travel tips"]):
        return "travel"

    return "general"


# -----------------------------
# EXTRACT TRAVEL INFORMATION
# -----------------------------
def extract_travel_info(message):

    info = {}

    destination_match = re.search(r"to (\w+)", message.lower())
    budget_match = re.search(r"(\d+)\s?(rs|rupees|budget)", message.lower())

    if destination_match:
        info["destination"] = destination_match.group(1)

    if budget_match:
        info["budget"] = budget_match.group(1)

    return info


# -----------------------------
# CHATBOT RESPONSE
# -----------------------------
def ask_travel_bot(user_message, session_id):

    intent = detect_intent(user_message)
    travel_data = extract_travel_info(user_message)

    if session_id not in conversation_memory:
        conversation_memory[session_id] = {}

    conversation_memory[session_id].update(travel_data)

    system_prompt = """
You are TravelMatch AI.

You help users with two things:

1. Travel Assistant
- suggest destinations
- create itineraries
- suggest budget tips
- suggest activities

2. Matchmaking Assistant
- help users find compatible travel partners
- ask questions to understand preferences

When helping with matchmaking ask about:
destination
travel date
budget
interests
gender preference
travel style

Be friendly and conversational.
Keep answers short and helpful.
"""

    if intent == "matchmaking":

        bot_instruction = """
The user wants a travel partner.

Ask questions to gather:
destination
travel date
budget
interests
gender preference
Guide the user step by step.
"""

    elif intent == "travel":

        bot_instruction = """
The user wants travel help.

Provide:
destination suggestions
itinerary ideas
budget tips
activities
"""

    else:

        bot_instruction = """
Continue friendly conversation and ask about the user's travel plans.
"""

    full_prompt = f"""
{system_prompt}

{bot_instruction}

User message:
{user_message}
"""

    response = model.generate_content(full_prompt)

    return response.text


# -----------------------------
# ROUTES
# -----------------------------
@app.route('/')
def home():
    return render_template('index.html')


@app.route('/get_response', methods=['POST'])
def get_bot_response():

    data = request.json
    user_message = data.get("message")

    session_id = "default_user"

    bot_response = ask_travel_bot(user_message, session_id)

    return jsonify({
        "response": bot_response
    })


# -----------------------------
# RUN SERVER
# -----------------------------
if __name__ == '__main__':
    app.run(debug=True)