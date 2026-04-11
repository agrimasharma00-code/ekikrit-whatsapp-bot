import anthropic
import json
import os
from schemes import match_schemes, format_schemes_for_whatsapp
from profile import save_user, save_matched_schemes
from scheduler import schedule_onboarding_reminders

client = anthropic.Anthropic(api_key=os.getenv("ANTHROPIC_API_KEY"))

QUESTIONS = [
    ("age",         "What is your age? (just a number)"),
    ("income",      "What is your monthly income in rupees? (just a number)"),
    ("state",       "Which state do you live in?"),
    ("family_size", "How many people live in your house? (just a number)"),
    ("occupation",  "What is your occupation? (e.g. farmer, construction worker, daily wage, student, vendor)"),
    ("caste",       "What is your caste category? (General / OBC / SC / ST)"),
]

SYSTEM_PROMPT = """You are Ekikrit, a helpful Indian government scheme assistant on WhatsApp.

Your job:
1. DETECT the language the user is writing in (Hindi, English, Tamil, Bengali, Hinglish, etc.)
2. ALWAYS reply in that SAME language — mirror it exactly
3. If someone writes in Hinglish (mixed Hindi-English), reply in Hinglish
4. Be warm, simple, and clear — users may be from rural or semi-urban areas
5. Ask ONE question at a time
6. If user input is unclear or invalid, ask again gently in the same language

Special commands to handle:
- If user says 'voice on' or 'awaaz mein bolo' → acknowledge voice mode is ON
- If user says 'voice off' → acknowledge voice mode is OFF
- If user says 'restart' or 'dobara' or 'phir se' → restart the conversation
- If user says 'status' or 'meri yojana' → tell them to check their matched schemes

Never switch languages unless the user does first."""

async def detect_lang_code(text: str) -> str:
    for char in text:
        cp = ord(char)
        if 0x0900 <= cp <= 0x097F: return "hi"
        if 0x0B80 <= cp <= 0x0BFF: return "ta"
        if 0x0980 <= cp <= 0x09FF: return "bn"
        if 0x0C00 <= cp <= 0x0C7F: return "te"
        if 0x0A80 <= cp <= 0x0AFF: return "gu"
        if 0x0C80 <= cp <= 0x0CFF: return "kn"
        if 0x0A00 <= cp <= 0x0A7F: return "pa"
    return "en"

async def ask_question(index: int, history: list, user_msg: str) -> str:
    _, q_en = QUESTIONS[index]
    response = client.messages.create(
        model="claude-sonnet-4-20250514",
        max_tokens=150,
        system=SYSTEM_PROMPT,
        messages=history + [{"role": "user", "content": (
            f"Ask this question in the same language the user is using: '{q_en}'. "
            f"Just the question, nothing else."
        )}]
    )
    return response.content[0].text.strip()

async def validate_input(field: str, value: str) -> tuple:
    if field in ("age", "income", "family_size"):
        digits = ''.join(filter(str.isdigit, value))
        return (bool(digits), digits)
    return (True, value.strip())

async def get_agent_reply(user_msg: str, state: dict, phone: str = "") -> str:
    step    = state["step"]
    history = state["history"]
    profile = state["profile"]

    msg_lower = user_msg.lower()

    if any(x in msg_lower for x in ["voice on", "awaaz mein", "audio on"]):
        state["voice_mode"] = True
        save_user(phone, state)
        return "Voice mode ON! Ab main aapko audio message bhi bhejoonga."

    if any(x in msg_lower for x in ["voice off", "audio off", "text only"]):
        state["voice_mode"] = False
        save_user(phone, state)
        return "Voice mode OFF. Ab sirf text messages milenge."

    if any(x in msg_lower for x in ["restart", "dobara", "phir se", "reset", "start again"]):
        state["step"]    = "start"
        state["profile"] = {}
        state["history"] = []
        save_user(phone, state)
        return await get_agent_reply("hi", state, phone)

    lang = await detect_lang_code(user_msg)
    if lang != "en":
        state["lang_code"] = lang

    history.append({"role": "user", "content": user_msg})

    if step == "start":
        response = client.messages.create(
            model="claude-sonnet-4-20250514",
            max_tokens=300,
            system=SYSTEM_PROMPT,
            messages=history + [{"role": "user", "content": (
                "The user just started. Greet them warmly as Ekikrit in the SAME language. "
                "Tell them you help find government schemes. Then ask their age. Under 3 lines."
            )}]
        )
        reply = response.content[0].text.strip()
        state["step"] = "age"
        history.append({"role": "assistant", "content": reply})
        save_user(phone, state)
        return reply

    field_names = [q[0] for q in QUESTIONS]
    if step in field_names:
        idx   = field_names.index(step)
        field = QUESTIONS[idx][0]

        valid, cleaned = await validate_input(field, user_msg)
        if not valid:
            response = client.messages.create(
                model="claude-sonnet-4-20250514",
                max_tokens=100,
                system=SYSTEM_PROMPT,
                messages=history + [{"role": "user", "content": (
                    f"User gave invalid input for '{field}' needs a number. "
                    f"Politely ask again in same language. One sentence only."
                )}]
            )
            reply = response.content[0].text.strip()
            history.append({"role": "assistant", "content": reply})
            save_user(phone, state)
            return reply

        profile[field] = cleaned

        if idx + 1 < len(QUESTIONS):
            state["step"] = QUESTIONS[idx + 1][0]
            reply = await ask_question(idx + 1, history, user_msg)
        else:
            state["step"] = "done"
            reply = await generate_results(profile, history, phone, state)

        history.append({"role": "assistant", "content": reply})
        save_user(phone, state)
        return reply

    if step == "done":
        response = client.messages.create(
            model="claude-sonnet-4-20250514",
            max_tokens=300,
            system=SYSTEM_PROMPT,
            messages=history + [{"role": "user", "content": (
                "User sent a message after receiving results. "
                "Answer helpfully in the same language. "
                "If they ask about a specific scheme, explain it. "
                "If they ask about documents, help them. "
                "Remind them to type 'restart' to check again."
            )}]
        )
        reply = response.content[0].text.strip()
        history.append({"role": "assistant", "content": reply})
        save_user(phone, state)
        return reply

    return "Kuch gadbad ho gayi. 'restart' type karein please."

async def generate_results(profile: dict, history: list, phone: str, state: dict) -> str:
    matched = match_schemes(
        age=profile.get("age", "0"),
        income=profile.get("income", "0"),
        occupation=profile.get("occupation", ""),
        caste=profile.get("caste", ""),
        state=profile.get("state", ""),
        family_size=profile.get("family_size", "1")
    )

    ngrok_url = os.getenv("NGROK_URL", "https://yourngrok.ngrok.io")

    if matched and phone:
        save_matched_schemes(phone, matched)
        lang = state.get("lang_code", "hi")
        schedule_onboarding_reminders(phone, [s["name"] for s in matched], lang)

    if matched:
        schemes_text = format_schemes_for_whatsapp(matched)
        prompt = (
            f"User profile: {json.dumps(profile)}\n"
            f"Eligible schemes:\n{schemes_text}\n\n"
            f"In the SAME language the user was writing in:\n"
            f"1. Congratulate warmly\n"
            f"2. Say how many schemes ({len(matched)}) they qualify for\n"
            f"3. List each with name, key benefit, and 2 documents\n"
            f"4. Tell them they will get automatic reminders on this number\n"
            f"5. End with: Aur jaankari ke liye: {ngrok_url}\n"
            f"6. Say go to nearest CSC centre to apply\n"
            f"Keep readable on mobile. Minimal emojis."
        )
    else:
        prompt = (
            f"User profile: {json.dumps(profile)}\n"
            f"No schemes matched. In same language:\n"
            f"1. Apologise gently\n"
            f"2. Suggest CSC centre visit\n"
            f"3. Share: {ngrok_url}\n"
            f"4. Type 'restart' to try again"
        )

    response = client.messages.create(
        model="claude-sonnet-4-20250514",
        max_tokens=900,
        system=SYSTEM_PROMPT,
        messages=history + [{"role": "user", "content": prompt}]
    )
    return response.content[0].text.strip()