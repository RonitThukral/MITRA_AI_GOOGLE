from typing import List, Dict
from datetime import datetime
from pathlib import Path
import json

from config import CRISIS_LOG, SESSION_STATES

def ensure_session_state(session_id: str) -> Dict:
    """Ensure a session state exists for the given session ID."""
    if session_id not in SESSION_STATES:
        SESSION_STATES[session_id] = {
            "history": [],
            "mode": "text",
            "career_suggest_active": False
        }
    return SESSION_STATES[session_id]

def trim_history(history: List[Dict], max_items: int = 8) -> List[Dict]:
    """Trim conversation history to the last max_items entries."""
    return history[-max_items:]

def build_prompt(system_prompt: str, context: str, history: List[Dict], user_message: str) -> str:
    """Build a prompt for regular chat without search results."""
    parts = []
    parts.append("SYSTEM INSTRUCTIONS:\n" + system_prompt.strip())
    if context:
        parts.append("\nCONTEXT / FACTS:\n" + context.strip())
    if history:
        history_block = "\nCONVERSATION HISTORY (most recent last):\n"
        for m in history:
            role = m.get("role", "user").upper()
            text = m.get("text", "")
            history_block += f"{role}: {text}\n"
        parts.append(history_block.strip())
    parts.append("\nUSER:\n" + user_message.strip())
    parts.append("\nASSISTANT:")
    return "\n\n".join(parts)

def build_prompt_with_search_results(system_prompt: str, search_context: str, history: List[Dict], user_message: str) -> str:
    """Build a prompt incorporating search results."""
    parts = []
    parts.append("SYSTEM INSTRUCTIONS:\n" + system_prompt.strip())
    
    if search_context:
        parts.append("\n" + "="*50)
        parts.append("WEB SEARCH RESULTS (USE THIS CURRENT INFORMATION):")
        parts.append("="*50)
        parts.append(search_context.strip())
        parts.append("="*50)
    
    if history:
        parts.append("\nRECENT CONVERSATION:")
        for m in history[-4:]:
            role = m.get("role", "user").upper()
            text = m.get("text", "")[:150]
            parts.append(f"{role}: {text}")
    
    parts.append(f"\nCURRENT USER QUESTION: {user_message.strip()}")
    
    if search_context:
        parts.append("\nIMPORTANT: Use the web search results above to provide current, accurate information. Start your response by acknowledging you searched the web.")
    
    return "\n\n".join(parts)

def log_crisis_event(session_id: str, message: str):
    """Log a crisis event to a JSONL file."""
    try:
        CRISIS_LOG.parent.mkdir(parents=True, exist_ok=True)
        with open(CRISIS_LOG, "a", encoding="utf-8") as f:
            entry = {"session_id": session_id, "message": message, "timestamp": datetime.now().isoformat()}
            f.write(json.dumps(entry, ensure_ascii=False) + "\n")
    except Exception:
        pass