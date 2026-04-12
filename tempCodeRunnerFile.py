from fastapi import FastAPI, Request
from twilio.twiml.messaging_response import MessagingResponse
import json

app = FastAPI()

# Store user states (temporary memory)
user_states = {}

# Load schemes
with open("schemes.json") as f:
    schemes = json.load(f)

# Function to match schemes
def match_schemes(income):
    eligible = []
    for s in schemes:
        if int(income) < s["income_limit"]:
            eligible.append(s["name"])
    return eligible

@app.post("/webhook")
async def whatsapp_webhook(request: Request):
    data = await request.form()
    msg = data.get("Body")
    user = data.get("From")

    response = MessagingResponse()
    reply = response.message()

    # Initialize user
    if user not in user_states:
        user_states[user] = {"step": "start"}

    state = user_states[user]

    # Conversation flow
    if state["step"] == "start":
        reply.body("Namaste 🙏\nAapki age kya hai?")
        state["step"] = "age"

    elif state["step"] == "age":
        state["age"] = msg
        reply.body("Aapki monthly income kya hai?")
        state["step"] = "income"

    elif state["step"] == "income":
        state["income"] = msg
        reply.body("Aap kis state se hain?")
        state["step"] = "state"

    elif state["step"] == "state":
        state["state"] = msg
        reply.body("Aapka occupation kya hai?")
        state["step"] = "occupation"

    elif state["step"] == "occupation":
        state["occupation"] = msg

        # Match schemes
        income = int(state["income"])
        result = match_schemes(income)

        if result:
            schemes_text = "\n".join(result)
            reply.body(f"🎉 Aap in yojanaon ke liye eligible hain:\n\n{schemes_text}")
        else:
            reply.body("❌ Koi scheme match nahi hui.")

        # Reset
        user_states[user] = {"step": "start"}

    return str(response)

print(schemes)
