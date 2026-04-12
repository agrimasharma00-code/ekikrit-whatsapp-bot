from deep_translator import GoogleTranslator

LANGUAGES = {
    "1": ("hi", "Hindi"),
    "2": ("bn", "Bengali"),
    "3": ("ta", "Tamil"),
    "4": ("te", "Telugu"),
    "5": ("mr", "Marathi"),
    "6": ("gu", "Gujarati"),
    "7": ("en", "English"),
}

def translate(text, lang_code):
    if lang_code == "en":
        return text
    try:
        translated = GoogleTranslator(source='auto', target=lang_code).translate(text)
        return translated
    except Exception as e:
        print(f"Translation error: {e}")
        return text