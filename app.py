import os
import torch
from transformers import Blip2Processor, Blip2ForConditionalGeneration
from PIL import Image
import requests
from bs4 import BeautifulSoup
import gradio as gr


print("🔄 Loading BLIP2 model... (this may take some time)")  # Load BLIP2 model

processor = Blip2Processor.from_pretrained("Salesforce/blip2-flan-t5-xl")
model = Blip2ForConditionalGeneration.from_pretrained(
    "Salesforce/blip2-flan-t5-xl",
    torch_dtype=torch.float32,
    device_map="auto"   # accelerate handles CPU/GPU split
)

print("✅ Model loaded successfully with accelerate device_map")

# -----------------------------
# Google Search Helper
# -----------------------------
def google_search(query, num_results=3):
    try:
        url = f"https://www.google.com/search?q={query}"
        headers = {"User-Agent": "Mozilla/5.0"}
        response = requests.get(url, headers=headers)
        soup = BeautifulSoup(response.text, "html.parser")

        results = []
        for g in soup.find_all("div", class_="BNeawe s3v9rd AP7Wnd")[:num_results]:
            results.append(g.get_text())
        return results if results else ["❌ No detailed info found"]
    except Exception as e:
        return [f"⚠️ Search error: {e}"]

# -----------------------------
# Memory-based Chat
# -----------------------------
chat_history = []  # stores (user, bot) messages

def chatbot(user_input, image=None):
    global chat_history

    if image:
        # If user uploaded an image → use BLIP2
        try:
            image = image.convert("RGB")
            context = " ".join([f"User: {u} Bot: {b}" for u, b in chat_history[-5:]])  # last 5 turns
            prompt = context + f" User asks: {user_input}"
            inputs = processor(images=image, text=prompt, return_tensors="pt")
            inputs = {k: v.to(model.device) for k, v in inputs.items()}

            generated_ids = model.generate(**inputs, max_new_tokens=100)
            answer = processor.batch_decode(generated_ids, skip_special_tokens=True)[0].strip()

            if answer.lower() in ["i don't know", "unknown", "not sure", ""]:
                search_results = google_search(user_input)
                answer += "\n\n🔍 Google says:\n" + "\n".join(search_results)
        except Exception as e:
            answer = f"⚠️ Error: {e}"
    else:
        # Text-only → do Google search
        search_results = google_search(user_input)
        answer = "🔍 Google says:\n" + "\n".join(search_results)

    # Save to history
    chat_history.append((user_input, answer))
    return chat_history, chat_history

# -----------------------------
# Gradio UI with Chatbot
# -----------------------------
with gr.Blocks() as demo:
    gr.Markdown("# 🤖 Smart Image + Text Chatbot with Memory")

    chatbot_ui = gr.Chatbot(label="Conversation")
    msg = gr.Textbox(label="Ask something")
    img = gr.Image(type="pil", label="Optional: Upload an Image")
    clear = gr.Button("Clear Chat")

    def clear_history():
        global chat_history
        chat_history = []
        return [], []

    msg.submit(chatbot, inputs=[msg, img], outputs=[chatbot_ui, chatbot_ui])
    clear.click(clear_history, outputs=[chatbot_ui, chatbot_ui])

# -----------------------------
# Run server
# -----------------------------
if __name__ == "__main__":
    demo.launch(server_name="0.0.0.0", server_port=7860)
