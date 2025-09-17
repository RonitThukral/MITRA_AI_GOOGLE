import base64
from fastapi import FastAPI, Request, Form, WebSocket, WebSocketDisconnect
from fastapi.responses import HTMLResponse, JSONResponse
from fastapi.templating import Jinja2Templates
from fastapi.staticfiles import StaticFiles
from pathlib import Path
import uvicorn

from config import TEMPLATES_DIR, PROJECT_ID, LOCATION, MODEL_NAME, SYSTEM_PROMPTS, CRISIS_RESPONSE
from utils import ensure_session_state, build_prompt, build_prompt_with_search_results, trim_history, log_crisis_event
from search import should_perform_web_search, build_optimized_search_query, perform_web_search
from models import MODEL, tools
from live_session import gemini_live_session_handler
from google.cloud import texttospeech

app = FastAPI()
templates = Jinja2Templates(directory=TEMPLATES_DIR)

# Mount static files if directory exists
if Path("static").exists():
    app.mount("/static", StaticFiles(directory="static"), name="static")

@app.get("/", response_class=HTMLResponse)
async def home(request: Request):
    return templates.TemplateResponse("index.html", {"request": request})

@app.websocket("/live-session")
async def websocket_endpoint(websocket: WebSocket):
    """WebSocket endpoint for Gemini Live API sessions"""
    await gemini_live_session_handler(websocket)

@app.post("/chat")
async def chat(
    message: str = Form(...),
    session_id: str = Form("default"),
    system_key: str = Form("mental_health_wellness"),
    context: str = Form(""),
    career_suggest: bool = Form(False),
    post_live_session: bool = Form(False)
):
    try:
        session_state = ensure_session_state(session_id)
        current_mode = session_state["mode"]
        session_state["career_suggest_active"] = career_suggest



        # Handle post-live session check-in
        if post_live_session:
            check_in_message = "Are you feeling fine now? How was our live session together?"
            session_state["mode"] = "voice_assistant"  # Force voice mode for check-in
            
            # Generate TTS response
            tts_client = texttospeech.TextToSpeechClient()
            voice_config = texttospeech.VoiceSelectionParams(
                language_code="en-US", name="en-US-Wavenet-F", 
                ssml_gender=texttospeech.SsmlVoiceGender.FEMALE
            )
            audio_config = texttospeech.AudioConfig(
                audio_encoding=texttospeech.AudioEncoding.MP3
            )
            synthesis_input = texttospeech.SynthesisInput(text=check_in_message)
            tts_response = tts_client.synthesize_speech(
                input=synthesis_input, voice=voice_config, audio_config=audio_config
            )
            base64_audio = base64.b64encode(tts_response.audio_content).decode('utf-8')
            
            # Update history
            session_state["history"].append({"role": "assistant", "text": check_in_message})
            
            return JSONResponse({
                "mode": "voice_assistant",
                "audio": base64_audio,
                "text_reply": check_in_message,
                "career_suggest_active": career_suggest,
                "search_performed": False,
                "post_live_checkin": True
            })



        # Determine if web search is needed
        needs_search = should_perform_web_search(message, career_suggest)
        search_context = ""
        search_source = None

        print(f"📝 Message: {message}")
        print(f"🎯 Career mode: {career_suggest}, Needs search: {needs_search}")

        if career_suggest:
            system_key = "career_suggest"
            if needs_search:
                print("🔍 Performing web search...")
                search_query = build_optimized_search_query(message)
                search_results, search_source = await perform_web_search(search_query, 6)
                
                if search_results:
                    print(f"✅ Search successful: {len(search_results)} results from {search_source}")
                    search_context = f"SEARCH QUERY: '{search_query}'\nSOURCE: {search_source}\n\n"
                    for i, result in enumerate(search_results, 1):
                        search_context += f"RESULT {i}:\n"
                        search_context += f"Title: {result['title']}\n"
                        search_context += f"Content: {result['snippet']}\n"
                        search_context += f"Source: {result.get('source', 'Web')}\n"
                        if result.get('link'):
                            search_context += f"URL: {result['link']}\n"
                        search_context += "\n"
                else:
                    print("❌ Search failed")
                    search_context = "WEB SEARCH ATTEMPTED but no results found. Provide general guidance and suggest checking official websites.\n\n"
            else:
                print("ℹ️ No search needed for this query")

        # Crisis detection for mental health mode only
        if not career_suggest:
            try:
                call_response = MODEL.generate_content(message, tools=[tools])
                
                if (call_response.candidates and 
                    call_response.candidates[0].content.parts and
                    hasattr(call_response.candidates[0].content.parts[0], 'function_call') and
                    call_response.candidates[0].content.parts[0].function_call):
                    
                    tool_call = call_response.candidates[0].content.parts[0].function_call

                    if tool_call.name == "handle_crisis_situation" and current_mode == "text":
                        log_crisis_event(session_id, message)
                        session_state["mode"] = "voice_assistant"

                        # Generate TTS response for crisis
                        tts_client = texttospeech.TextToSpeechClient()
                        voice_config = texttospeech.VoiceSelectionParams(
                            language_code="en-US", name="en-US-Wavenet-F", 
                            ssml_gender=texttospeech.SsmlVoiceGender.FEMALE
                        )
                        audio_config = texttospeech.AudioConfig(
                            audio_encoding=texttospeech.AudioEncoding.MP3
                        )
                        synthesis_input = texttospeech.SynthesisInput(text=CRISIS_RESPONSE)
                        tts_response = tts_client.synthesize_speech(
                            input=synthesis_input, voice=voice_config, audio_config=audio_config
                        )
                        base64_audio = base64.b64encode(tts_response.audio_content).decode('utf-8')
                        
                        session_state["history"].append({"role": "user", "text": message})
                        session_state["history"].append({"role": "assistant", "text": CRISIS_RESPONSE})
                        
                        return JSONResponse({
                            "mode": "voice_assistant",
                            "audio": base64_audio,
                            "text_reply": CRISIS_RESPONSE,
                            "career_suggest_active": career_suggest,
                            "search_performed": False,
                            "crisis_detected": True
                        })

                    elif tool_call.name == "handle_calm_situation" and current_mode == "voice_assistant":
                        session_state["mode"] = "text"
                        reply = "I'm glad to hear you're feeling better. We can continue our conversation through text."
                        session_state["history"].append({"role": "user", "text": message})
                        session_state["history"].append({"role": "assistant", "text": reply})
                        return JSONResponse({
                            "mode": "text", 
                            "reply": reply,
                            "career_suggest_active": career_suggest,
                            "search_performed": False
                        })
            except Exception as tool_error:
                print(f"⚠️ Tool error: {tool_error}")

        # Generate main response using search results
        system_prompt = SYSTEM_PROMPTS.get(system_key) or SYSTEM_PROMPTS.get("mental_health_wellness")
        history = trim_history(session_state["history"], 6)
        
        # Build prompt with search results
        if needs_search and search_context:
            full_prompt = build_prompt_with_search_results(system_prompt, search_context, history, message)
        else:
            full_prompt = build_prompt(system_prompt=system_prompt, context=context, history=history, user_message=message)

        print("🤖 Generating response...")
        response = MODEL.generate_content([full_prompt])
        reply = getattr(response, "text", None)
        
        if not reply:
            reply = "I apologize, but I'm having trouble generating a response right now. Please try again."

        print(f"✅ Response generated: {len(reply)} characters")

        # Update conversation history
        session_state["history"].append({"role": "user", "text": message})
        session_state["history"].append({"role": "assistant", "text": reply})

        # Handle voice mode response
        if current_mode == "voice_assistant":
            tts_client = texttospeech.TextToSpeechClient()
            voice_config = texttospeech.VoiceSelectionParams(
                language_code="en-US", name="en-US-Wavenet-F", 
                ssml_gender=texttospeech.SsmlVoiceGender.FEMALE
            )
            audio_config = texttospeech.AudioConfig(
                audio_encoding=texttospeech.AudioEncoding.MP3
            )
            synthesis_input = texttospeech.SynthesisInput(text=reply)
            tts_response = tts_client.synthesize_speech(
                input=synthesis_input, voice=voice_config, audio_config=audio_config
            )
            base64_audio = base64.b64encode(tts_response.audio_content).decode('utf-8')

            return JSONResponse({
                "mode": "voice_assistant",
                "audio": base64_audio,
                "text_reply": reply,
                "career_suggest_active": career_suggest,
                "search_performed": needs_search,
                "search_source": search_source
            })
        else:
            return JSONResponse({
                "reply": reply,
                "mode": "text", 
                "career_suggest_active": career_suggest,
                "search_performed": needs_search,
                "search_source": search_source
            })

    except Exception as e:
        print("🔥 Critical Error:", e)
        import traceback
        traceback.print_exc()
        return JSONResponse({
            "error": f"I encountered an error processing your request. Please try again.",
            "mode": "text",
            "career_suggest_active": career_suggest,
            "search_performed": False
        }, status_code=500)

@app.get("/test_search")




async def test_search(q: str = "JEE Main 2025 dates"):
    """Test endpoint to verify search functionality"""
    try:
        results, source = await perform_web_search(q, 3)
        return JSONResponse({
            "query": q,
            "source": source,
            "results_count": len(results),
            "results": results
        })
    except Exception as e:
        return JSONResponse({"error": str(e)}, status_code=500)

@app.get("/_debug/sessions", response_class=JSONResponse)
async def debug_sessions():
    from config import SESSION_STATES
    return JSONResponse({
        "sessions_count": len(SESSION_STATES), 
        "sessions": {
            k: {
                "messages": len(v["history"]), 
                "mode": v["mode"], 
                "career_active": v.get("career_suggest_active", False)
            } for k, v in SESSION_STATES.items()
        }
    })

@app.get("/health")
async def health_check():
    from config import SERPAPI_KEY, GOOGLE_CSE_API_KEY, GOOGLE_CSE_ID
    return {
        "status": "healthy", 
        "model": MODEL_NAME,
        "search_apis": {
            "serpapi": "configured" if SERPAPI_KEY else "missing",
            "google_cse": "configured" if (GOOGLE_CSE_API_KEY and GOOGLE_CSE_ID) else "missing"
        }
    }

if __name__ == "__main__":
    uvicorn.run(app, host="0.0.0.0", port=8000)











































