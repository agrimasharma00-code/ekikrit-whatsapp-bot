import os
import anthropic
from apscheduler.schedulers.asyncio import AsyncIOScheduler
from twilio.rest import Client
from datetime import datetime, timedelta
from profile import (
    get_conn, get_due_messages, mark_message_sent,
    get_followup_due, mark_followup_sent, schedule_message
)

twilio_client = Client(os.getenv("TWILIO_ACCOUNT_SID"), os.getenv("TWILIO_AUTH_TOKEN"))
claude_client  = anthropic.Anthropic(api_key=os.getenv("ANTHROPIC_API_KEY"))
SANDBOX_NUMBER = os.getenv("TWILIO_WHATSAPP_NUMBER", "whatsapp:+14155238886")

scheduler = AsyncIOScheduler()

def send_whatsapp(to: str, body: str):
    try:
        twilio_client.messages.create(
            from_=SANDBOX_NUMBER,
            to=to,
            body=body
        )
        print(f"[Scheduler] Sent to {to}: {body[:60]}...")
    except Exception as e:
        print(f"[Scheduler] Send error: {e}")

async def check_scheduled_messages():
    """Send any messages that are due right now."""
    due = get_due_messages()
    for msg in due:
        send_whatsapp(msg["phone"], msg["message"])
        mark_message_sent(msg["id"])

async def check_followups():
    """Send follow-up messages to users 12 days after scheme matching."""
    due = get_followup_due()

    seen_phones = set()
    for row in due:
        phone = row["phone"]
        if phone in seen_phones:
            continue
        seen_phones.add(phone)

        conn = get_conn()
        schemes = conn.execute("""
            SELECT scheme_name FROM matched_schemes
            WHERE phone=? AND status='suggested'
        """, (phone,)).fetchall()
        user_row = conn.execute("SELECT lang_code FROM users WHERE phone=?", (phone,)).fetchone()
        conn.close()

        scheme_names = [s["scheme_name"] for s in schemes]
        lang = user_row["lang_code"] if user_row else "hi"

        prompt = (
            f"You are Ekikrit, a friendly government scheme assistant. "
            f"The user was told about these schemes 12 days ago: {', '.join(scheme_names)}. "
            f"Send a warm, short follow-up message in {'Hindi' if lang == 'hi' else 'English'} asking: "
            f"1) Did they manage to apply? "
            f"2) Do they need help with documents? "
            f"3) Remind them they can reply anytime for help. "
            f"Keep it under 3 sentences. Warm and simple tone."
        )

        response = claude_client.messages.create(
            model="claude-sonnet-4-20250514",
            max_tokens=200,
            messages=[{"role": "user", "content": prompt}]
        )
        msg = response.content[0].text.strip()
        send_whatsapp(phone, msg)
        mark_followup_sent(phone)

async def check_scheme_deadlines():
    """
    Check schemes.json for upcoming deadlines and
    send reminders to users who matched those schemes.
    """
    import json
    with open("schemes.json", encoding="utf-8") as f:
        schemes = json.load(f)

    today = datetime.now().date()

    for scheme in schemes:
        last_date = scheme.get("last_date")
        days_before = scheme.get("reminder_days_before", 7)
        if not last_date:
            continue

        deadline = datetime.strptime(last_date, "%Y-%m-%d").date()
        remind_on = deadline - timedelta(days=days_before)

        if remind_on != today:
            continue

        conn = get_conn()
        users = conn.execute("""
            SELECT DISTINCT m.phone, u.lang_code
            FROM matched_schemes m
            JOIN users u ON u.phone = m.phone
            WHERE m.scheme_name=? AND m.status='suggested'
        """, (scheme["name"],)).fetchall()
        conn.close()

        for user in users:
            phone = user["phone"]
            lang  = user["lang_code"] or "hi"
            days_left = (deadline - today).days

            prompt = (
                f"You are Ekikrit. Send an urgent but friendly reminder in {'Hindi' if lang=='hi' else 'English'} that: "
                f"Scheme '{scheme['name']}' has only {days_left} days left to apply (deadline: {last_date}). "
                f"Tell them to go to nearest CSC centre or visit {scheme.get('apply_link', 'official portal')}. "
                f"Keep it under 4 sentences. Add urgency but stay calm."
            )

            response = claude_client.messages.create(
                model="claude-sonnet-4-20250514",
                max_tokens=200,
                messages=[{"role": "user", "content": prompt}]
            )
            msg = response.content[0].text.strip()
            send_whatsapp(phone, msg)

def schedule_onboarding_reminders(phone: str, scheme_names: list, lang: str = "hi"):
    """
    Call this right after a user gets their scheme results.
    Schedules: Day 3 tip, Day 7 nudge, Day 12 full follow-up (handled by check_followups).
    """
    now = datetime.now()
    schemes_str = ", ".join(scheme_names[:3])

    if lang == "hi":
        day3_msg = (
            f"Namaste! Ekikrit se yaad dila rahe hain — "
            f"aap {schemes_str} ke liye eligible hain. "
            f"Nearest CSC centre mein jaake apply karna na bhoolen. Koi sawaal ho toh yahan likhein!"
        )
        day7_msg = (
            f"Ek hafte ho gaya! Kya aapne {scheme_names[0] if scheme_names else 'yojana'} ke liye apply kiya? "
            f"Agar documents mein koi dikkat aa rahi hai toh humse poochein — bilkul free!"
        )
    else:
        day3_msg = (
            f"Hello! Ekikrit reminder — you are eligible for {schemes_str}. "
            f"Visit your nearest CSC centre to apply. Reply here if you need help!"
        )
        day7_msg = (
            f"One week gone! Did you apply for {scheme_names[0] if scheme_names else 'the scheme'}? "
            f"If you face any document issues, just reply here — we're happy to help!"
        )

    schedule_message(phone, day3_msg, now + timedelta(days=3),  "day3_reminder")
    schedule_message(phone, day7_msg, now + timedelta(days=7),  "day7_nudge")

def start_scheduler():
    scheduler.add_job(check_scheduled_messages, "interval", minutes=30, id="scheduled_msgs")
    scheduler.add_job(check_followups,          "cron",     hour=9, minute=0, id="followups")
    scheduler.add_job(check_scheme_deadlines,   "cron",     hour=9, minute=15, id="deadlines")
    scheduler.start()
    print("[Scheduler] Started — reminders, follow-ups, deadlines active.")