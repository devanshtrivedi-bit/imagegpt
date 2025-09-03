import streamlit as st
from transformers import AutoImageProcessor, AutoModelForImageClassification
from PIL import Image
import torch

# ---------------------------
# Knowledge Base
# ---------------------------
knowledge_base = {
    "corn": {
        "common rust": "Cause: Fungus (Puccinia sorghi). Symptoms: reddish-brown pustules on leaves. Control: resistant varieties, fungicides.",
        "gray leaf spot": "Cause: Fungus (Cercospora zeae-maydis). Symptoms: gray rectangular lesions. Control: resistant hybrids, fungicides.",
        "leaf blight": "Cause: Fungus (Exserohilum turcicum). Symptoms: cigar-shaped lesions. Control: resistant hybrids, fungicides.",
        "healthy": "Green leaves, no lesions, normal growth."
    },
    "potato": {
        "early blight": "Cause: Fungus (Alternaria solani). Symptoms: concentric dark spots. Control: crop rotation, fungicides.",
        "late blight": "Cause: Oomycete (Phytophthora infestans). Symptoms: water-soaked lesions, white mold. Control: resistant varieties, fungicides.",
        "healthy": "Green leaves, no dark spots."
    },
    "rice": {
        "brown spot": "Cause: Fungus (Bipolaris oryzae). Symptoms: brown circular spots with yellow halo. Control: seed treatment, fungicides.",
        "hispa": "Cause: Insect (Dicladispa armigera). Symptoms: scraping on leaves, small holes. Control: insecticides, resistant varieties.",
        "leaf blast": "Cause: Fungus (Magnaporthe oryzae). Symptoms: diamond-shaped lesions. Control: resistant varieties, fungicides.",
        "healthy": "No lesions, normal green leaves."
    },
    "wheat": {
        "brown rust": "Cause: Fungus (Puccinia triticina). Symptoms: orange-brown pustules. Control: resistant varieties, fungicides.",
        "yellow rust": "Cause: Fungus (Puccinia striiformis). Symptoms: yellow stripes of pustules. Control: resistant varieties, fungicides.",
        "healthy": "Uniform green leaves, no pustules."
    }
}

# ---------------------------
# Load Model with Caching and Spinner
# ---------------------------
@st.cache_resource
def load_model():
    processor = AutoImageProcessor.from_pretrained(
        "wambugu71/crop_leaf_diseases_vit", use_fast=True
    )
    model = AutoModelForImageClassification.from_pretrained(
        "wambugu71/crop_leaf_diseases_vit"
    )
    return processor, model

with st.spinner("Loading model... this may take 10-20 seconds"):
    processor, model = load_model()

# ---------------------------
# Streamlit UI
# ---------------------------
st.title("🌿 Crop Disease Detector + Chatbot")
st.write("Upload a leaf image to detect disease, then ask questions about it.")

# --- Image Upload ---
uploaded_file = st.file_uploader("Upload a leaf image...", type=["jpg", "jpeg", "png"])
detected_label = None

if uploaded_file is not None:
    image = Image.open(uploaded_file)
    st.image(image, caption="Uploaded Image", use_container_width=True)

    with st.spinner("Predicting disease..."):
        # Prediction
        inputs = processor(images=image, return_tensors="pt")
        with torch.no_grad():
            outputs = model(**inputs)

        logits = outputs.logits
        predicted_class_id = logits.argmax(-1).item()
        detected_label = model.config.id2label[predicted_class_id].lower()

    st.success(f"✅ Detected class: {detected_label.capitalize()}")

    # Give quick info if available
    for crop, diseases in knowledge_base.items():
        if detected_label in diseases:
            st.info(f"ℹ️ {crop.capitalize()} - {detected_label.capitalize()}: {diseases[detected_label]}")
            break

# --- Chatbot ---
st.subheader("💬 Chat with Crop Bot")
user_input = st.text_input("Ask about a crop or disease:")

if user_input:
    query = user_input.lower()
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
    st.text_area("Bot:", value=response, height=150)
