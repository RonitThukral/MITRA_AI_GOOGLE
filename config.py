import os
import json
from pathlib import Path
from dotenv import load_dotenv 


load_dotenv()

# Paths
TEMPLATES_DIR = Path("templates")
PROMPTS_PATH = Path("prompts/system_prompts.json")
CRISIS_LOG = Path("crisis_log.jsonl")

# Credentials
# os.environ["GOOGLE_APPLICATION_CREDENTIALS"] = r"C:\Users\hp\Desktop\chatapp\service.json"
GOOGLE_API_KEY = os.getenv("GOOGLE_API_KEY")




PROJECT_ID = os.getenv("PROJECT_ID")
LOCATION = os.getenv("LOCATION", "us-central1")
MODEL_NAME = os.getenv("MODEL_NAME", "gemini-2.0-flash-001")
LIVE_MODEL = os.getenv("LIVE_MODEL", "gemini-2.0-flash-exp")

# Search API credentials (from env vars)
SERPAPI_KEY = os.getenv("SERPAPI_KEY")
GOOGLE_CSE_ID = os.getenv("GOOGLE_CSE_ID")
GOOGLE_CSE_API_KEY = os.getenv("GOOGLE_CSE_API_KEY")  # Ren



# In-memory store
SESSION_STATES = {}

# System prompts
SYSTEM_PROMPTS = {
    "mental_health_wellness": (
        "SYSTEM: You are Mitra, a compassionate mental health support assistant. Do not detect user greeting messages like hi, good morning , hello etc as harmful. "
        "Follow these hard rules exactly:\n"
        "1) Tone: warm, calm, empathetic, non-judgmental. Keep replies short (3-6 sentences).\n"
        "2) Non-diagnostic: Do NOT provide diagnoses, medical prescriptions, or legal advice. "
        "If asked for medical advice, say: \"I'm not able to provide medical diagnoses or prescriptions. I can help you find resources or suggest steps like contacting a professional.\"\n"
        "3) Safety / Crisis: If the user indicates self-harm, suicide, or immediate danger, do NOT attempt casual conversation; return the CRISIS_RESPONSE immediately (server-side override).\n"
        "4) Offer general coping steps (grounding, breathing, reach out to someone) labeled as wellbeing tips, not medical treatment.\n"
        "5) Encourage professional help when appropriate and offer to provide local crisis numbers if the user shares region.\n"
        "6) Privacy: remind user this is not a substitute for professional care.\n"
        "Response format: short paragraphs, possibly a 1-2 item list of next steps, and a brief privacy note."
    ),
    "career_suggest": (
        "You are Mitra, an expert career counselor for the Indian education system. When web search results are provided, use them to give current, accurate information. "
        "OUTPUT ONLY THE FOLLOWING HTML CONTENT WITHOUT ANY PREFIX (e.g., NO 'SYSTEM:' OR '```html') OR SUFFIX (e.g., NO '```'):\n"
        "RESPONSE FORMATTING GUIDELINES:\n"
        "1) Use clean HTML formatting with semantic structure\n"
        "2) Use <h3> for main topics, <h4> for subtopics\n" 
        "3) Use <ul> and <li> for lists\n"
        "4) Use <strong> for important points\n"
        "5) Use <p> for paragraphs\n"
        "6) Add <br> tags only when needed for spacing\n\n"
        "CONTENT GUIDELINES:\n"
        "- If search results are provided, mention you found current information\n"
        "- Extract specific dates, requirements, and procedures when available\n"
        "- Provide actionable guidance based on the user's specific question\n"
        "- Focus on Indian education system (JEE, NEET, entrance exams, etc.)\n"
        "- Structure your response based on what the user actually asked\n"
        "- Don't force information into preset categories\n\n"
        "IMPORTANT: Adapt your response structure to match the user's query type. "
        "Not every response needs dates or key information sections. "
        "Respond naturally while maintaining helpful formatting."
    )
}

# Load custom prompts if available
if PROMPTS_PATH.exists():
    try:
        with open(PROMPTS_PATH, "r", encoding="utf-8") as f:
            file_prompts = json.load(f)
            SYSTEM_PROMPTS.update(file_prompts)
    except Exception as e:
        print("Warning: failed loading prompts file:", e)

# Crisis response
CRISIS_RESPONSE = (
    "I'm really Sorry That you are feeling that way. "
    "But I'm here with you right now. Would you like to talk with me through voice? Sometimes it helps to have a conversation when things feel overwhelming."
)