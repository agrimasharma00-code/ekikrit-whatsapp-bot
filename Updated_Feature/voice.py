import os
import requests
import tempfile
from gtts import gTTS
from openai import OpenAI

openai_client = OpenAI(api_key=os.getenv("OPENAI_API_KEY"))

TWILIO_ACCOUNT_SID = os.getenv("TWILIO_ACCOUNT_SID")
TWILIO_AUTH_TOKEN  = os.getenv("TWILIO_AUTH_TOKEN")
NGROK_URL          = os.getenv("NGROK_URL", "http://localhost:8000")

LANG_TO_GTTS = {
    "hi": "hi",   # Hindi
    "en": "en",   # English
    "ta": "ta",   # Tamil
    "bn": "bn",   # Bengali
    "te": "te",   # Telugu
    "mr": "mr",   # Marathi
    "gu": "gu",   # Gujarati
    "kn": "kn",   # Kannada
    "pa": "pa",   # Punjabi
    "ur": "ur",   # Urdu
}

def detect_lang_code(history: list) -> str:
    """
    Peek at conversation history to guess language code for gTTS.
    Default Hindi since most users will be Hindi speakers.
    """
    for msg in reversed(history):
        content = msg.get("content", "")
        if any(ord(c) > 0x0900 and ord(c) < 0x097F for c in content):
            return "hi"
        if any(ord(c) > 0x0B80 and ord(c) < 0x0BFF for c in content):
            return "ta"
        if any(ord(c) > 0x0980 and ord(c) < 0x09FF for c in content):
            return "bn"
    return "hi"

async def transcribe_voice(media_url: str) -> str:
    """
    Download audio from Twilio MediaUrl and transcribe via Whisper.
    Twilio requires auth to download media.
    """
    response = requests.get(
        media_url,
        auth=(TWILIO_ACCOUNT_SID, TWILIO_AUTH_TOKEN)
    )
    if response.status_code != 200:
        return ""

    with tempfile.NamedTemporaryFile(suffix=".ogg", delete=False) as f:
        f.write(response.content)
        tmp_path = f.name

    try:
        with open(tmp_path, "rb") as audio_file:
            transcript = openai_client.audio.transcriptions.create(
                model="whisper-1",
                file=audio_file,
                language=None  # auto-detect language
            )
        return transcript.text.strip()
    except Exception as e:
        print(f"Whisper transcription error: {e}")
        return ""
    finally:
        os.unlink(tmp_path)

def text_to_speech(text: str, lang_code: str = "hi") -> str | None:
    """
    Convert text to MP3 using gTTS. Save to static/audio/ folder.
    Returns the public URL or None on failure.
    """
    gtts_lang = LANG_TO_GTTS.get(lang_code, "hi")
    audio_dir = "static/audio"
    os.makedirs(audio_dir, exist_ok=True)

    import hashlib, time
    filename = hashlib.md5(f"{text[:50]}{time.time()}".encode()).hexdigest() + ".mp3"
    filepath = os.path.join(audio_dir, filename)

    try:
        tts = gTTS(text=text, lang=gtts_lang, slow=False)
        tts.save(filepath)
        public_url = f"{NGROK_URL}/audio/{filename}"
        return public_url
    except Exception as e:
        print(f"gTTS error: {e}")
        return None

def clean_for_speech(text: str) -> str:
    """
    Remove markdown, URLs, emojis for cleaner TTS output.
    """
    import re
    text = re.sub(r'http\S+', '', text)
    text = re.sub(r'\*+', '', text)
    text = re.sub(r'#+ ', '', text)
    text = re.sub(r'[\U00010000-\U0010ffff]', '', text, flags=re.UNICODE)
    text = re.sub(r'\n+', '. ', text)
    text = re.sub(r'\s+', ' ', text)
    return text.strip()