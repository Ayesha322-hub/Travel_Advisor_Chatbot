import gradio as gr
import os
import requests

# === Load environment variables safely ===
GROQ_API_KEY = os.environ.get("GROQ_API_KEY")
if not GROQ_API_KEY:
    print("⚠️ GROQ_API_KEY not set. Set it in Hugging Face 'Secrets' tab.")
    GROQ_API_KEY = "sk-fake-for-testing"  # Optional fallback for dev

# === GROQ API config ===
GROQ_API_URL = "https://api.groq.com/openai/v1/chat/completions"
MODEL_NAME = "llama3-8b-8192"

# === System prompt for the chatbot ===
SYSTEM_PROMPT = """You are a friendly and helpful travel advisor.
You answer user questions about travel destinations, planning, and tips in a clear and engaging way."""

def query_groq(message, history):
    import sys

    # Check if API key is loaded
    if not GROQ_API_KEY or not GROQ_API_KEY.startswith("gsk_"):
        print("🚫 GROQ_API_KEY is missing or invalid.", file=sys.stderr)
        return "GROQ_API_KEY is missing or invalid. Please check Hugging Face Secrets."

    headers = {
        "Authorization": f"Bearer {GROQ_API_KEY}",
        "Content-Type": "application/json"
    }

    # Log headers without exposing full key
    print(f"🔐 Authorization header present: {'Authorization' in headers and headers['Authorization'].startswith('Bearer gsk_')}", file=sys.stderr)

    messages = [{"role": "system", "content": SYSTEM_PROMPT}]
    for user_msg, bot_msg in history:
        messages.append({"role": "user", "content": user_msg})
        messages.append({"role": "assistant", "content": bot_msg})

    messages.append({"role": "user", "content": message})

    payload = {
        "model": MODEL_NAME,
        "messages": messages,
        "temperature": 0.7
    }

    try:
        response = requests.post(GROQ_API_URL, headers=headers, json=payload)

        print(f"📡 Request sent to GROQ. Status code: {response.status_code}", file=sys.stderr)

        if response.status_code == 200:
            return response.json()["choices"][0]["message"]["content"].strip()
        else:
            print("❌ GROQ API Error:", response.text, file=sys.stderr)
            return f"❌ GROQ API Error {response.status_code}: {response.text}"

    except Exception as e:
        print(f"💥 Exception during GROQ request: {str(e)}", file=sys.stderr)
        return f"⚠️ Failed to call GROQ API: {str(e)}"

# === Custom chatbot function ===
def custom_respond(condition, region, restrictions, chat_history):
    if not isinstance(chat_history, list):
        chat_history = []

    user_msg = f"Condition: {condition}\nRegion: {region}\nRestrictions: {', '.join(restrictions) if restrictions else 'None'}"
    bot_msg = query_groq(user_msg, chat_history)

    chat_history.append([user_msg, bot_msg])  # ✅ List of lists for Gradio
    return chat_history, chat_history

# === Gradio interface ===
with gr.Blocks() as demo:
    gr.Markdown("## 🏖️ Travel Advisor Chatbot")

    condition = gr.Dropdown(
        ["Beach", "Mountain", "City", "Countryside"],
        label="Destination Type",
        value="Beach"
    )

    region = gr.Dropdown(
        ["North America", "South Asia", "Europe", "Middle East"],
        label="Region",
        value="North America"
    )

    restrictions = gr.CheckboxGroup(
        ["Budget-Friendly", "Luxury", "Family-Friendly", "Romantic"],
        label="Preferences"
    )

    chatbot = gr.Chatbot(type="messages")  # Use 'messages' type instead of 'tuples'
    state = gr.State([])  # ✅ Always a list

    with gr.Row():
        submit = gr.Button("Get Travel Plan")
        clear = gr.Button("Clear Chat")

    submit.click(fn=custom_respond, inputs=[condition, region, restrictions, state], outputs=[chatbot, state])
    clear.click(lambda: ([], []), None, outputs=[chatbot, state])

demo.launch()
