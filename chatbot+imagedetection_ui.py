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
          background: #f0fdf4;
          margin: 0; padding: 0;
          display: flex; justify-content: center; align-items: center;
          min-height: 100vh;
          transition: background 0.3s, color 0.3s;
        }
        body.dark { background: #1f2937; color: #e5e7eb; }
        .container {
          width: 100%; max-width: 700px;
          background: white;
          padding: 2rem;
          border-radius: 20px;
          box-shadow: 0 8px 24px rgba(0,0,0,0.1);
          transition: background 0.3s, color 0.3s;
        }
        body.dark .container { background: #111827; color: #f9fafb; }
        h1 { color: #166534; text-align:center; margin-bottom: 1rem; }
        body.dark h1 { color: #22c55e; }
        .topbar { display:flex; justify-content:flex-end; margin-bottom:1rem; }
        .toggle-btn {
          background:none; border:none; font-size:1.5rem; cursor:pointer;
        }
        .upload-label {
          background: #22c55e; color: white;
          padding: 12px 20px; border-radius: 30px;
          cursor: pointer; display:inline-block;
          text-align:center;
          transition: background 0.3s;
        }
        .upload-label:hover { background: #15803d; }
        input[type=file] { display:none; }
        img { margin-top:1rem; max-width:100%; border-radius:12px; }
        .card {
          margin-top: 1rem; padding:1rem;
          border-radius:12px;
          background:#f9fafb; border:1px solid #e5e7eb;
          transition: background 0.3s, border 0.3s;
        }
        body.dark .card { background:#1f2937; border:1px solid #374151; }
        .prediction {
          background:#f0fdf4; border:1px solid #bbf7d0; color:#065f46;
        }
        body.dark .prediction { background:#064e3b; border:1px solid #047857; color:#a7f3d0; }
        .chat-input {
          width:100%; padding:10px;
          border:1px solid #ccc; border-radius:8px;
          margin-top:0.5rem;
          background:white;
          transition: background 0.3s, color 0.3s, border 0.3s;
        }
        body.dark .chat-input { background:#374151; color:white; border:1px solid #4b5563; }
        .btn {
          margin-top:0.5rem; padding:10px 20px;
          border:none; border-radius:8px;
          background:#22c55e; color:white; cursor:pointer;
          transition: background 0.3s;
        }
        .btn:hover { background:#15803d; }
        footer {
          margin-top: 2rem;
          text-align:center;
          font-size: 0.9rem;
          color: #6b7280;
        }
        body.dark footer { color:#9ca3af; }
      </style>
    </head>
    <body>
      <div class="container">
        <div class="topbar">
          <button id="mode-toggle" class="toggle-btn">🌙</button>
        </div>
        <h1>🌱 Smart Crop Assistant</h1>
        <p style="text-align:center; color:#374151;">Upload a crop leaf image to detect diseases and chat with the bot for advice.</p>

        <!-- Image Upload -->
        <div class="section">
          <label for="file-upload" class="upload-label">📷 Upload Leaf Image</label>
          <input id="file-upload" type="file" accept="image/*">
          <div id="preview"></div>
          <div id="result" class="card prediction" style="display:none;"></div>
        </div>

        <!-- Chatbot -->
        <div class="section card">
          <h3>💬 Chat with Crop Bot</h3>
          <input id="chat-input" class="chat-input" placeholder="Ask about a crop or disease...">
          <button class="btn" onclick="askBot()">Send</button>
          <div id="chat-response" style="margin-top:1rem;"></div>
        </div>

        <!-- Coming Soon -->
        <div class="section card">
          <h3>🚧 Coming Soon</h3>
          <ul>
            <li>🌦 Weather-based alerts</li>
            <li>📊 Market price tracking</li>
            <li>🎤 Voice support for farmers</li>
            <li>📝 Feedback collection</li>
          </ul>
        </div>

        <footer>© 2025 Krishi Sevak  | Built with ❤️ for Farmers by Team yantragya</footer>
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
            previewDiv.innerHTML = `<img src="${e.target.result}" alt="Leaf Preview">`;
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
          document.getElementById("chat-response").innerText = data.response;
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
