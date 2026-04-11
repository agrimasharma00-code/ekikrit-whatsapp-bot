import os
from fastapi import FastAPI, Request
from fastapi.responses import Response, FileResponse
from fastapi.staticfiles import StaticFiles
from twilio.twiml.messaging_response import MessagingResponse
from contextlib import asynccontextmanager

from agent import get_agent_reply
from profile import get_user, save_user
from voice import transcribe_voice, text_to_speech, clean_for_speech
from scheduler import start_scheduler

@asynccontextmanager
async def lifespan(app: FastAPI):
    start_scheduler()
    yield

app = FastAPI(lifespan=lifespan)

os.makedirs("static/audio", exist_ok=True)
app.mount("/audio", StaticFiles(directory="static/audio"), name="audio")

def load_state(phone: str) -> dict:
    saved = get_user(phone)
    if saved:
        return saved
    return {
        "step":       "start",
        "history":    [],
        "profile":    {},
        "lang_code":  "hi",
        "voice_mode": False,
    }

@app.post("/webhook")
async def whatsapp_webhook(request: Request):
    data       = await request.form()
    user_msg   = data.get("Body", "").strip()
    phone      = data.get("From", "")
    media_url  = data.get("MediaUrl0", None)
    media_type = data.get("MediaContentType0", "")

    state = load_state(phone)
    transcribed = False

    if media_url and "audio" in media_type:
        transcribed_text = await transcribe_voice(media_url)
        if transcribed_text:
            user_msg    = transcribed_text
            transcribed = True
        else:
            user_msg = "voice message"

    if not user_msg:
        user_msg = "hello"

    reply_text = await get_agent_reply(user_msg, state, phone)

    response = MessagingResponse()
    msg      = response.message()

    voice_mode = state.get("voice_mode", False)

    if voice_mode or transcribed:
        lang_code   = state.get("lang_code", "hi")
        clean_reply = clean_for_speech(reply_text)
        audio_url   = text_to_speech(clean_reply, lang_code)
        if audio_url:
            msg.body(reply_text)
            msg.media(audio_url)
        else:
            msg.body(reply_text)
    else:
        msg.body(reply_text)

    return Response(content=str(response), media_type="application/xml")

@app.get("/")
def home():
    return FileResponse("index.html")