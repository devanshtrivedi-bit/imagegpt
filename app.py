from transformers import AutoImageProcessor, AutoModelForImageClassification
from PIL import Image
import torch

# Load processor and model
processor = AutoImageProcessor.from_pretrained("wambugu71/crop_leaf_diseases_vit")
model = AutoModelForImageClassification.from_pretrained("wambugu71/crop_leaf_diseases_vit")

# Load an image (replace 'test_leaf.jpg' with your image path)
image = Image.open(r"D:\image proccesing minor project\datasets\Train\Healthy Wheat\2KS7HG.jpg")


# Preprocess image
inputs = processor(images=image, return_tensors="pt")

# Forward pass
with torch.no_grad():
    outputs = model(**inputs)

# Get logits and predicted class
logits = outputs.logits
predicted_class_id = logits.argmax(-1).item()

# Map to class name
label = model.config.id2label[predicted_class_id]

print(f"Predicted class: {label}")
