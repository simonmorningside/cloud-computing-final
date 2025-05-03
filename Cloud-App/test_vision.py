from google.cloud import vision

# Initialize client
client = vision.ImageAnnotatorClient()

# Public image URL to test
image_uri = "https://upload.wikimedia.org/wikipedia/commons/4/47/PNG_transparency_demonstration_1.png"

# Create Image object
image = vision.Image()
image.source.image_uri = image_uri

# Call the Vision API
response = client.label_detection(image=image)

# Output detected labels
print("Detected labels:")
for label in response.label_annotations:
    print(f"- {label.description} (score: {label.score:.2f})")
