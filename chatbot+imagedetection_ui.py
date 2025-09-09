from flask import Flask, request, jsonify, Response
from transformers import AutoImageProcessor, AutoModelForImageClassification
from PIL import Image
import torch

# ---------------------------
# Knowledge Base
# ---------------------------
knowledge_base = {
    "corn": {"common rust": "Cause: Fungus (Puccinia sorghi). Symptoms: reddish-brown pustules on leaves. Control: resistant varieties, fungicides.",
             "gray leaf spot": "Cause: Fungus (Cercospora zeae-maydis). Symptoms: gray rectangular lesions. Control: resistant hybrids, fungicides.",
             "leaf blight": "Cause: Fungus (Exserohilum turcicum). Symptoms: cigar-shaped lesions. Control: resistant hybrids, fungicides.",
             "healthy": "Green leaves, no lesions, normal growth."},
    "potato": {"early blight": "Cause: Fungus (Alternaria solani). Symptoms: concentric dark spots. Control: crop rotation, fungicides.",
               "late blight": "Cause: Oomycete (Phytophthora infestans). Symptoms: water-soaked lesions, white mold. Control: resistant varieties, fungicides.",
               "healthy": "Green leaves, no dark spots."},
    "rice": {"brown spot": "Cause: Fungus (Bipolaris oryzae). Symptoms: brown circular spots with yellow halo. Control: seed treatment, fungicides.",
             "hispa": "Cause: Insect (Dicladispa armigera). Symptoms: scraping on leaves, small holes. Control: insecticides, resistant varieties.",
             "leaf blast": "Cause: Fungus (Magnaporthe oryzae). Symptoms: diamond-shaped lesions. Control: resistant varieties, fungicides.",
             "healthy": "No lesions, normal green leaves."},
    "wheat": {"brown rust": "Cause: Fungus (Puccinia triticina). Symptoms: orange-brown pustules. Control: resistant varieties, fungicides.",
              "yellow rust": "Cause: Fungus (Puccinia striiformis). Symptoms: yellow stripes of pustules. Control: resistant varieties, fungicides.",
              "healthy": "Uniform green leaves, no pustules."}
}

# ---------------------------
# Load Model
# ---------------------------
processor = AutoImageProcessor.from_pretrained("wambugu71/crop_leaf_diseases_vit")
model = AutoModelForImageClassification.from_pretrained("wambugu71/crop_leaf_diseases_vit")

# ---------------------------
# Flask App
# ---------------------------
from flask import Flask, Response

app = Flask(__name__)

@app.route("/")
def index():
    html = """
    <!DOCTYPE html>
    <html lang="en">
    <head>
      <meta charset="UTF-8">
      <meta name="viewport" content="width=device-width, initial-scale=1.0">
      <title>🌱 Smart Crop Assistant</title>
      <style>
        body {
          font-family: 'Segoe UI', sans-serif;
          background: linear-gradient(135deg, #064e3b, #166534, #22c55e);
          margin: 0; padding: 0;
          min-height: 100vh;
          display: flex; justify-content: center; align-items: center;
          color: #f9fafb;
        }

        /* Glassmorphic Container */
        .container {
          width: 100%; max-width: 950px;
          background: rgba(255, 255, 255, 0.08);
          backdrop-filter: blur(16px);
          border-radius: 24px;
          padding: 2rem;
          box-shadow: 0 8px 40px rgba(0,0,0,0.4);
          border: 1px solid rgba(255,255,255,0.2);
        }

        /* Navbar */
        .topbar {
          display:flex; justify-content:space-between; align-items:center;
          margin-bottom: 2rem;
        }
        .logo {
          font-size: 1.5rem;
          font-weight: bold;
          color: #22c55e;
          text-shadow: 0 0 8px #22c55e;
        }
        .toggle-btn {
          background:none; border:none; font-size:1.8rem; cursor:pointer;
          color: #f9fafb;
        }

        h1 {
          text-align:center;
          font-size: 2.2rem;
          background: linear-gradient(90deg, #22c55e, #4ade80, #a7f3d0);
          -webkit-background-clip: text;
          -webkit-text-fill-color: transparent;
          margin-bottom: 0.5rem;
        }
        .subtitle {
          text-align:center;
          font-size: 1.1rem;
          color:#d1d5db;
          margin-bottom: 2rem;
        }

        /* Upload Section */
        .upload-section {
          display: flex;
          flex-direction: column;
          align-items: center;
          justify-content: center;
          margin: 1.5rem 0;
          text-align: center;
        }
        .upload-box {
          border: 2px dashed rgba(34,197,94,0.8);
          border-radius: 20px;
          padding: 2.5rem;
          text-align: center;
          cursor: pointer;
          background: rgba(34,197,94,0.05);
          transition: all 0.3s ease;
          width: 100%;
          max-width: 500px;
        }
        .upload-box:hover {
          background: rgba(34,197,94,0.15);
          transform: scale(1.02);
          border-color:#4ade80;
          box-shadow: 0 0 20px rgba(34,197,94,0.4);
        }
        input[type=file] { display:none; }
        #preview {
          margin-top:1rem;
          max-width: 500px;
          text-align: center;
        }
        .preview-img {
          max-width: 300px;
          border-radius:16px;
          margin-top: 1rem;
        }

        /* Prediction Box */
        #result {
          width: 100%;
          max-width: 500px;
          text-align: center;
        }
        .prediction {
          background: rgba(16,185,129,0.1);
          border:1px solid #10b981;
          padding:1rem;
          border-radius:16px;
          margin-top:1rem;
          color:#a7f3d0;
          box-shadow: inset 0 0 20px rgba(16,185,129,0.3);
        }

        /* Chat Section */
        .card {
          margin-top: 2rem;
          padding:1.5rem;
          border-radius:20px;
          background: rgba(255,255,255,0.05);
          border:1px solid rgba(255,255,255,0.2);
        }

        .chat-box {
          max-height:300px;
          overflow-y:auto;
          margin-top:1rem;
          padding:0.5rem;
        }
        .chat-msg {
          padding:10px 16px;
          margin:10px 0;
          border-radius:16px;
          max-width:80%;
          font-size:0.95rem;
          animation: fadeIn 0.5s ease;
        }
        .chat-user {
          background: linear-gradient(135deg, #22c55e, #16a34a);
          color:white;
          margin-left:auto;
          text-align:right;
          box-shadow:0 0 12px rgba(34,197,94,0.5);
        }
        .chat-bot {
          background: rgba(255,255,255,0.15);
          color:#f9fafb;
          margin-right:auto;
        }

        @keyframes fadeIn {
          from { opacity:0; transform:translateY(10px); }
          to { opacity:1; transform:translateY(0); }
        }

        .chat-input {
          width:100%; padding:12px;
          border-radius:12px;
          border:none;
          margin-top:0.8rem;
          background: rgba(255,255,255,0.1);
          color:white;
          font-size:1rem;
        }
        .btn {
          margin-top:1rem;
          padding:12px 28px;
          border:none; border-radius:12px;
          background: linear-gradient(135deg, #22c55e, #4ade80);
          color:white; cursor:pointer; font-size:1rem;
          transition: transform 0.3s ease, box-shadow 0.3s ease;
        }
        .btn:hover {
          transform: scale(1.05);
          box-shadow: 0 0 20px rgba(34,197,94,0.6);
        }

        /* Footer */
        footer {
          margin-top: 2rem;
          text-align:center;
          font-size: 0.85rem;
          color: #9ca3af;
        }
      </style>
    </head>
    <body>
      <div class="container">
        <!-- Navbar -->
        <div class="topbar">
          <div class="logo">🌾 KrishiSevak</div>
          <button id="mode-toggle" class="toggle-btn">🌙</button>
        </div>

        <h1>Smart Crop Assistant</h1>
        <p class="subtitle">AI-Powered Farming • Disease Detection • Smart Chatbot</p>

        <!-- Upload Section -->
        <div class="upload-section">
          <label for="file-upload" class="upload-box">
            🌿 Drop your crop leaf image here or click to upload
            <input id="file-upload" type="file" accept="image/*">
          </label>
          <div id="preview"></div>
          <div id="result" class="prediction" style="display:none;"></div>
        </div>

        <!-- Chatbot -->
        <div class="card">
          <h3>🤖 Ask Krishi Bot</h3>
          <div id="chat-box" class="chat-box"></div>
          <input id="chat-input" class="chat-input" placeholder="Type your farming question...">
          <button class="btn" onclick="askBot()">Send</button>
        </div>

        <!-- Coming Soon -->
        <div class="card">
          <h3>🔮 Future Features</h3>
          <ul>
            <li>🌦 Real-time weather + disease alerts</li>
            <li>📊 AI-based yield + price prediction</li>
            <li>🎤 Voice-enabled farmer assistant</li>
            <li>🛰 Satellite + IoT crop monitoring</li>
          </ul>
        </div>

        <footer>© 2025 Krishi Sevak | Built with ⚡ Future Tech for Farmers (SIH)</footer>
      </div>

      <script>
        // Dark mode toggle
        const toggleBtn = document.getElementById("mode-toggle");
        toggleBtn.addEventListener("click", () => {
          document.body.classList.toggle("dark");
          toggleBtn.textContent = document.body.classList.contains("dark") ? "☀️" : "🌙";
        });

        // File Upload + Prediction
        const fileInput = document.getElementById("file-upload");
        const previewDiv = document.getElementById("preview");
        const resultDiv = document.getElementById("result");

        fileInput.addEventListener("change", async () => {
          const file = fileInput.files[0];
          if (!file) return;

          const reader = new FileReader();
          reader.onload = (e) => {
            previewDiv.innerHTML = `<img src="${e.target.result}" alt="Leaf Preview" class="preview-img">`;
          };
          reader.readAsDataURL(file);

          const formData = new FormData();
          formData.append("file", file);

          const response = await fetch("/predict", { method: "POST", body: formData });
          const data = await response.json();

          resultDiv.style.display = "block";
          resultDiv.innerHTML = `<h3>🩺 Prediction: ${data.prediction}</h3>`;
        });

        // Chatbot
        async function askBot() {
          const query = document.getElementById("chat-input").value;
          if (!query) return;

          const response = await fetch("/chat", {
            method: "POST",
            headers: { "Content-Type": "application/json" },
            body: JSON.stringify({ query: query })
          });
          const data = await response.json();

          const chatBox = document.getElementById("chat-box");
          chatBox.innerHTML += `<div class="chat-msg chat-user">${query}</div>`;

          // Typing animation for bot
          const botMsg = document.createElement("div");
          botMsg.classList.add("chat-msg", "chat-bot");
          chatBox.appendChild(botMsg);

          let i = 0;
          const text = data.response;
          const typing = setInterval(() => {
            botMsg.textContent = text.slice(0, i++);
            if (i > text.length) clearInterval(typing);
            chatBox.scrollTop = chatBox.scrollHeight;
          }, 30);

          document.getElementById("chat-input").value = "";
        }
      </script>
    </body>
    </html>
    """
    return Response(html, mimetype="text/html")



# Prediction endpoint
@app.route("/predict", methods=["POST"])
def predict():
    file = request.files["file"]
    image = Image.open(file.stream).convert("RGB")
    inputs = processor(images=image, return_tensors="pt")
    with torch.no_grad():
        outputs = model(**inputs)
    logits = outputs.logits
    predicted_class_id = logits.argmax(-1).item()
    label = model.config.id2label[predicted_class_id].lower()
    return jsonify({"prediction": label})

# Chatbot endpoint
@app.route("/chat", methods=["POST"])
def chat():
    query = request.json.get("query", "").lower()
    response = "❌ Sorry, I don’t have info on that. Try asking about Corn, Potato, Rice, or Wheat."
    for crop, diseases in knowledge_base.items():
        if crop in query:
            for disease, info in diseases.items():
                if disease in query:
                    response = f"🌱 {crop.capitalize()} - {disease.capitalize()}:\n{info}"
                    break
            else:
                response = f"I know about these {crop} diseases: {', '.join(diseases.keys())}"
            break
    return jsonify({"response": response})

if __name__ == "__main__":
    app.run(debug=True)
