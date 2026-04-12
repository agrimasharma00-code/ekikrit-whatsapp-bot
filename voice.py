from gtts import gTTS

def text_to_voice(text, lang_code, filename="reply.mp3"):
    try:
        tts = gTTS(text=text, lang=lang_code)
        tts.save(filename)
        return filename
    except Exception as e:
        print(f"Voice error: {e}")
        return None