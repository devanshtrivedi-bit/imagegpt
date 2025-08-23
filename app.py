import io
import torch
from PIL import Image
import requests
from transformers import VisionEncoderDecoderModel, ViTImageProcessor, AutoTokenizer
import gradio as gr
import logging

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

print("Starting application...")

# Model Loading
MODEL_ID = "nlpconnect/vit-gpt2-image-captioning"

try:
    print("Loading model...")
    model = VisionEncoderDecoderModel.from_pretrained(MODEL_ID)
    processor = ViTImageProcessor.from_pretrained(MODEL_ID)
    tokenizer = AutoTokenizer.from_pretrained(MODEL_ID)

    device = torch.device("cuda" if torch.cuda.is_available() else "cpu")
    model.to(device)
    model.eval()
    print(f"Model loaded successfully on device: {device}")
except Exception as e:
    print(f"Error loading model: {e}")
    raise

def caption_image(image, max_length=16, num_beams=4):
    """Generate caption for image."""
    try:
        print("Processing image...")
        if image.mode != "RGB":
            image = image.convert("RGB")
        
        with torch.no_grad():
            pixel_values = processor(images=image, return_tensors="pt").pixel_values.to(device)
            output_ids = model.generate(
                pixel_values,
                max_length=max_length,
                num_beams=num_beams,
                early_stopping=True
            )
        
        caption = tokenizer.decode(output_ids[0], skip_special_tokens=True).strip()
        print(f"Generated caption: {caption}")
        return caption
    except Exception as e:
        error_msg = f"Error: {e}"
        print(error_msg)
        return error_msg

def caption_from_url(url, max_length=16, num_beams=4):
    """Generate caption from URL."""
    try:
        print(f"Fetching image from URL: {url}")
        resp = requests.get(url, timeout=30)
        image = Image.open(io.BytesIO(resp.content))
        return caption_image(image, max_length, num_beams)
    except Exception as e:
        error_msg = f"Error: {e}"
        print(error_msg)
        return error_msg

# Simple Gradio Interface
print("Creating Gradio interface...")

with gr.Blocks(title="Image Captioning Test") as demo:
    gr.Markdown("# Image Captioning Test")
    
    with gr.Tab("Upload"):
        img = gr.Image(type="pil")
        max_len_u = gr.Slider(8, 32, 16, label="Max Length")
        beams_u = gr.Slider(1, 4, 2, label="Beams")
        btn_u = gr.Button("Generate")
        out_u = gr.Textbox(label="Caption")
        btn_u.click(caption_image, [img, max_len_u, beams_u], out_u)
    
    with gr.Tab("URL"):
        url = gr.Textbox(label="Image URL")
        max_len = gr.Slider(8, 32, 16, label="Max Length")
        beams = gr.Slider(1, 4, 2, label="Beams")
        btn = gr.Button("Generate")
        out = gr.Textbox(label="Caption")
        btn.click(caption_from_url, [url, max_len, beams], out)

print("Interface created successfully")

if __name__ == "__main__":
    print("Starting server...")
    try:
        # Test the model first
        test_image = Image.new('RGB', (224, 224), color='red')
        test_result = caption_image(test_image, max_length=8, num_beams=1)
        print(f"Model test result: {test_result}")
        
        print("Launching Gradio...")
        demo.launch(
            server_name="0.0.0.0",
            server_port=7860,
            debug=True,
            show_error=True
        )
    except KeyboardInterrupt:
        print("Server stopped by user")
    except Exception as e:
        print(f"Server error: {e}")
        import traceback
        traceback.print_exc()
        input("Press Enter to exit...")
        