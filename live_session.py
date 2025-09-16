import json
import base64
import asyncio
from fastapi import WebSocket, WebSocketDisconnect
from google import genai
from config import LIVE_MODEL

genai_client = genai.Client(http_options={'api_version': 'v1alpha'})

async def gemini_live_session_handler(websocket: WebSocket):
    """Handles the Gemini Live API session for real-time voice interaction (continuous turns)."""
    await websocket.accept()
    try:
        # Receive initial setup/config message from client (must be sent by client first)
        config_message = await websocket.receive_text()
        try:
            config_data = json.loads(config_message)
            config = config_data.get("setup", {})
        except Exception:
            config = {}

        # Connect to Gemini Live
        async with genai_client.aio.live.connect(model=LIVE_MODEL, config=config) as session:
            print("Connected to Gemini Live API")

            # Send loop: read from client websocket and forward media chunks to Gemini Live
            async def send_to_gemini():
                try:
                    while True:
                        try:
                            msg = await websocket.receive_text()
                        except WebSocketDisconnect:
                            print("Client disconnected (send loop)")
                            break
                        except Exception as e:
                            print("receive_text error in send loop:", e)
                            break

                        # Parse and forward media chunks if present
                        try:
                            data = json.loads(msg)
                        except Exception:
                            continue

                        if "realtime_input" in data:
                            rt = data["realtime_input"]
                            if isinstance(rt, dict) and rt.get("action") == "commit":
                                continue

                            media_chunks = rt.get("media_chunks", []) if isinstance(rt, dict) else []
                            for chunk in media_chunks:
                                mime = chunk.get("mime_type")
                                body = chunk.get("data")
                                if not mime or not body:
                                    continue
                                try:
                                    await session.send_realtime_input(media={"mime_type": mime, "data": body})
                                except Exception as e:
                                    print("Failed to forward media chunk to Gemini:", e)
                except Exception as e:
                    print("send_to_gemini top-level error:", e)
                finally:
                    print("send_to_gemini finished")

            # Receive loop: read responses from Gemini Live and forward to client websocket
            async def receive_from_gemini():
                try:
                    while True:
                        try:
                            async for response in session.receive():
                                if response.server_content is None:
                                    continue

                                model_turn = response.server_content.model_turn
                                if model_turn:
                                    for part in model_turn.parts:
                                        if hasattr(part, "text") and part.text is not None:
                                            try:
                                                await websocket.send_text(json.dumps({"text": part.text}))
                                            except WebSocketDisconnect:
                                                print("Client disconnected while sending text part")
                                                return
                                            except Exception as e:
                                                print("Error sending text to client:", e)

                                        elif hasattr(part, "inline_data") and part.inline_data is not None:
                                            try:
                                                base64_audio = base64.b64encode(part.inline_data.data).decode("utf-8")
                                                await websocket.send_text(json.dumps({"audio": base64_audio}))
                                            except WebSocketDisconnect:
                                                print("Client disconnected while sending audio part")
                                                return
                                            except Exception as e:
                                                print("Error sending audio to client:", e)

                                if getattr(response.server_content, "turn_complete", False):
                                    print("<Turn complete> — waiting for next user input")
                        except Exception as inner_e:
                            print("Error while receiving from Gemini session:", inner_e)
                            break
                except Exception as e:
                    print("receive_from_gemini top-level error:", e)
                finally:
                    print("receive_from_gemini finished")

            # Run send and receive concurrently until one ends
            send_task = asyncio.create_task(send_to_gemini())
            receive_task = asyncio.create_task(receive_from_gemini())

            try:
                await asyncio.gather(send_task, receive_task)
            except Exception as e:
                print("Error in Gemini Live session tasks:", e)
            finally:
                for t in (send_task, receive_task):
                    if not t.done():
                        t.cancel()
                print("Gemini Live inner session finished")

    except WebSocketDisconnect:
        print("WebSocket disconnected (outer handler)")
    except Exception as e:
        print(f"Error in Gemini Live session handler: {e}")
        import traceback
        traceback.print_exc()
    finally:
        print("Gemini Live session closed")




























