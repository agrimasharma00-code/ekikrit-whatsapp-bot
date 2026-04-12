from fastapi import FastAPI, Request
from fastapi.responses import Response, FileResponse
from twilio.twiml.messaging_response import MessagingResponse
from twilio.rest import Client
import json
import threading
import time
import os
from translator import translate, LANGUAGES
from voice import text_to_voice
from twilio.twiml.voice_response import VoiceResponse, Gather

app = FastAPI()
user_states = {}

# ⚠️ SET THESE IN ENVIRONMENT VARIABLES OR .env FILE
TWILIO_SID = os.getenv("TWILIO_SID", "your_twilio_account_sid")
TWILIO_TOKEN = os.getenv("TWILIO_TOKEN", "your_twilio_auth_token")
TWILIO_WHATSAPP = os.getenv("TWILIO_WHATSAPP", "whatsapp:+14155238886")
YOUR_NGROK_URL = os.getenv("YOUR_NGROK_URL", "https://your-ngrok-url.ngrok-free.dev")

with open("schemes.json", encoding="utf-8") as f:
    schemes = json.load(f)

# ── STOP WORDS ──────────────────────────────────────────
STOP_WORDS = ["stop", "quit", "exit", "band karo", "bandh", "cancel", "ruko", "bas"]

def is_stop(msg):
    return msg.lower().strip() in STOP_WORDS

# ── PROGRESS BAR ────────────────────────────────────────
def progress_bar(current, total=6):
    filled = "█" * current
    empty = "░" * (total - current)
    return f"[{filled}{empty}] {current}/{total}"

# ── QUICK REPLY OPTIONS ──────────────────────────────────
def make_options(options_list):
    """Format options as numbered list for easy tap reply"""
    lines = []
    for i, opt in enumerate(options_list, 1):
        lines.append(f"{i}. {opt}")
    return "\n".join(lines)

# ── SCHEME MATCHING ──────────────────────────────────────
def match_schemes(age, income, occupation, caste):
    eligible = []
    income = int(income)
    age = int(age)
    occupation = occupation.lower().strip()
    caste = caste.lower().strip()
    for s in schemes:
        if income >= s["income_limit"]:
            continue
        if age < s["min_age"] or age > s["max_age"]:
            continue
        occ_match = "any" in s["occupations"] or any(
            o.lower() in occupation or occupation in o.lower()
            for o in s["occupations"]
        )
        if not occ_match:
            continue
        caste_match = "any" in s["castes"] or any(
            c.lower() == caste for c in s["castes"]
        )
        if not caste_match:
            continue
        eligible.append(s)
    return eligible

def format_schemes(schemes_list, lang):
    lines = []
    for i, s in enumerate(schemes_list, 1):
        lines.append(
            f"{i}. {s['name']}\n"
            f"   {translate('Benefit', lang)}: {s['benefit']}\n"
            f"   {translate('Documents', lang)}: {s['documents']}"
        )
    return "\n\n".join(lines)

def t(text, state):
    return translate(text, state.get("lang", "hi"))

# ── REMINDER SYSTEM ──────────────────────────────────────
def send_whatsapp_message(to, message):
    """Send a WhatsApp message via Twilio"""
    try:
        client = Client(TWILIO_SID, TWILIO_TOKEN)
        client.messages.create(
            from_=TWILIO_WHATSAPP,
            to=to,
            body=message
        )
        print(f"Reminder sent to {to}")
    except Exception as e:
        print(f"Reminder error: {e}")

def schedule_reminder(user, message, delay_seconds):
    """Schedule a reminder after delay"""
    def send_later():
        time.sleep(delay_seconds)
        send_whatsapp_message(user, message)
    thread = threading.Thread(target=send_later, daemon=True)
    thread.start()

# ── MAIN WEBHOOK ─────────────────────────────────────────
@app.post("/webhook")
async def whatsapp_webhook(request: Request):
    data = await request.form()
    msg = data.get("Body", "").strip()
    user = data.get("From", "")

    response = MessagingResponse()
    reply = response.message()

    if user not in user_states:
        user_states[user] = {"step": "start", "lang": "hi"}

    state = user_states[user]
    print(f"User: {user}, Step: {state['step']}, Msg: {msg}")

    # ── STOP COMMAND ─────────────────────────────────────
    if is_stop(msg) and state["step"] != "start":
        user_states[user] = {"step": "start", "lang": state.get("lang", "hi")}
        reply.body(t(
            "Okay, stopped! Send anything to start again anytime.",
            state
        ))
        return Response(content=str(response), media_type="application/xml")

    # ── VOICE REQUEST ─────────────────────────────────────
    if msg.lower() in ["voice", "audio", "bolo", "speak"]:
        if state.get("last_result"):
            lang = state.get("lang", "hi")
            voice_file = text_to_voice(state["last_result"], lang)
            if voice_file:
                audio_url = f"{YOUR_NGROK_URL}/audio/reply.mp3"
                reply.body(t("Here is your audio reply!", state))
                reply.media(audio_url)
            else:
                reply.body(t("Sorry, could not generate audio right now.", state))
        else:
            reply.body(t("Please complete the questions first.", state))
        return Response(content=str(response), media_type="application/xml")
    
    # CALL ME REQUEST
    if msg.lower() in ["call me", "call", "mujhe call karo", "phone karo"]:
        if state.get("last_result"):
            reply.body(t("Calling you now! Pick up in a few seconds!", state))
            threading.Thread(
                target=make_ai_call,
                args=(user.replace("whatsapp:", ""),),
                daemon=True
            ).start()
        else:
            reply.body(t("Complete the 6 questions first, then send 'call me'!", state))
        return Response(content=str(response), media_type="application/xml")

    # ── LANGUAGE SELECTION ────────────────────────────────
    if state["step"] == "start":
        reply.body(
            "Namaste! Main Ekikrit hoon 🙏\n"
            "Aapka AI Government Scheme Agent\n\n"
            "Choose language / Bhasha chunein:\n\n"
            "1. Hindi - हिंदी\n"
            "2. Bengali - বাংলা\n"
            "3. Tamil - தமிழ்\n"
            "4. Telugu - తెలుగు\n"
            "5. Marathi - मराठी\n"
            "6. Gujarati - ગુજરાતી\n"
            "7. English\n\n"
            "Reply with number (1-7)\n"
            "Send STOP anytime to quit"
        )
        state["step"] = "language"

    elif state["step"] == "language":
        if msg.strip() in LANGUAGES:
            lang_code, lang_name = LANGUAGES[msg.strip()]
            state["lang"] = lang_code
            reply.body(translate(
                f"Great! Speaking in {lang_name} now.\n\n"
                f"{progress_bar(1)}\n\n"
                "Question 1/6: What is your age?\n\n"
                "Reply with just the number\n"
                "Example: 43\n\n"
                "Send STOP anytime to quit",
                lang_code
            ))
            state["step"] = "age"
        else:
            reply.body(
                "Please reply with a number 1-7\n\n"
                "1. Hindi\n2. Bengali\n3. Tamil\n"
                "4. Telugu\n5. Marathi\n6. Gujarati\n7. English"
            )

    elif state["step"] == "age":
        if not msg.isdigit():
            reply.body(t(
                "Please send only a number!\n\nYour age? Example: 43",
                state
            ))
            return Response(content=str(response), media_type="application/xml")
        state["age"] = msg
        reply.body(t(
            f"Age saved!\n\n{progress_bar(2)}\n\n"
            "Question 2/6: Monthly income?\n\n"
            "Reply with amount in rupees\n"
            "Example: 8000\n\n"
            "Send STOP to quit",
            state
        ))
        state["step"] = "income"

    elif state["step"] == "income":
        if not msg.isdigit():
            reply.body(t(
                "Please send only a number!\n\nMonthly income? Example: 8000",
                state
            ))
            return Response(content=str(response), media_type="application/xml")
        state["income"] = msg
        reply.body(t(
            f"Income saved!\n\n{progress_bar(3)}\n\n"
            "Question 3/6: Which state?\n\n"
            "Example: Delhi / Bihar / UP / Maharashtra",
            state
        ))
        state["step"] = "state"

    elif state["step"] == "state":
        state["state"] = msg
        caste_options = make_options(["General", "OBC", "SC", "ST"])
        reply.body(t(
            f"State saved!\n\n{progress_bar(4)}\n\n"
            "Question 4/6: Family members?\n\n"
            "Reply with number\nExample: 4\n\n"
            "Send STOP to quit",
            state
        ))
        state["step"] = "family_size"

    elif state["step"] == "family_size":
        if not msg.isdigit():
            reply.body(t(
                "Please send only a number!\n\nFamily members? Example: 4",
                state
            ))
            return Response(content=str(response), media_type="application/xml")
        state["family_size"] = msg
        occ_options = make_options([
            "Construction worker",
            "Farmer",
            "Student",
            "Street vendor",
            "Daily wage worker",
            "Other"
        ])
        reply.body(t(
            f"Family size saved!\n\n{progress_bar(5)}\n\n"
            "Question 5/6: Your occupation?\n\n"
            f"{occ_options}\n\n"
            "Reply with number OR type your occupation\n\n"
            "Send STOP to quit",
            state
        ))
        state["step"] = "occupation"

    elif state["step"] == "occupation":
        occ_map = {
            "1": "construction worker",
            "2": "farmer",
            "3": "student",
            "4": "street vendor",
            "5": "daily wage",
            "6": "other"
        }
        state["occupation"] = occ_map.get(msg.strip(), msg)
        caste_options = make_options(["General", "OBC", "SC", "ST"])
        reply.body(t(
            f"Occupation saved!\n\n{progress_bar(6)}\n\n"
            "Question 6/6 - Last one!\n\n"
            "Your caste category?\n\n"
            f"{caste_options}\n\n"
            "Reply with number 1-4",
            state
        ))
        state["step"] = "caste"

    elif state["step"] == "caste":
        caste_map = {
            "1": "general",
            "2": "obc",
            "3": "sc",
            "4": "st"
        }
        state["caste"] = caste_map.get(msg.strip(), msg)

        matched = match_schemes(
            age=state["age"],
            income=state["income"],
            occupation=state["occupation"],
            caste=state["caste"]
        )

        if matched:
            result_intro = translate(
                f"Congratulations! You qualify for {len(matched)} schemes!",
                state["lang"]
            )
            formatted = format_schemes(matched, state["lang"])
            footer = translate(
                "To apply: Visit nearest CSC centre\n\n"
                "Send 'voice' for audio\n"
                "Send anything to check again",
                state["lang"]
            )
            full_reply = f"{result_intro}\n\n{formatted}\n\n{footer}"
            state["last_result"] = result_intro + "\n\n" + formatted
            reply.body(full_reply)

            # Schedule reminder after 2 minutes (for demo)
            # In production change to days
            reminder_msg = translate(
                f"Reminder from Ekikrit: You qualified for {len(matched)} schemes! "
                "Have you applied yet? Send 'hi' to check again.",
                state["lang"]
            )
            schedule_reminder(user, reminder_msg, delay_seconds=120)

        else:
            reply.body(t(
                "No schemes matched right now.\n\n"
                "Visit your nearest CSC centre for help.\n\n"
                "Send anything to try again.",
                state
            ))

        user_states[user] = {
            "step": "start",
            "lang": state["lang"],
            "last_result": state.get("last_result", "")
        }

    return Response(content=str(response), media_type="application/xml")

@app.get("/audio/{filename}")
def serve_audio(filename: str):
    return FileResponse(filename, media_type="audio/mpeg")

@app.post("/voice")
async def voice_webhook(request: Request):
    data = await request.form()
    digit = data.get("Digits", "")
    call_to = data.get("To", "")

    user_key = f"whatsapp:{call_to}"
    state = user_states.get(user_key, {})
    lang = state.get("lang", "hi")
    last_result = state.get("last_result", "")
    lang_code = "hi-IN" if lang == "hi" else "en-IN"

    vr = VoiceResponse()

    if digit == "1":
        vr.say(
            translate("Please visit your nearest Common Service Centre to apply. Thank you for using Ekikrit!", lang),
            language=lang_code
        )
        vr.hangup()

    elif digit == "2":
        gather = Gather(num_digits=1, action="/voice", method="POST")
        gather.say(last_result or "No results found.", language=lang_code)
        gather.say(translate("Press 1 to apply. Press 2 to hear again.", lang), language=lang_code)
        vr.append(gather)

    else:
        gather = Gather(num_digits=1, action="/voice", method="POST")
        gather.say(translate("Hello! This is Ekikrit. Here are your eligible government schemes.", lang), language=lang_code)
        gather.say(last_result or translate("Please WhatsApp us first to check schemes.", lang), language=lang_code)
        gather.say(translate("Press 1 to know how to apply. Press 2 to hear again.", lang), language=lang_code)
        vr.append(gather)

    return Response(content=str(vr), media_type="application/xml")

def make_ai_call(to_number):
    try:
        client = Client(TWILIO_SID, TWILIO_TOKEN)
        clean_number = to_number.replace("whatsapp:", "")
        call = client.calls.create(
            to=clean_number,
            from_="+16624813903",
            url=f"{YOUR_NGROK_URL}/voice"
        )
        print(f"Call initiated: {call.sid}")
    except Exception as e:
        print(f"Call error: {e}")

@app.get("/")
def home():
    return FileResponse("index.html")