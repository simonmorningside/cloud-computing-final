from flask import Flask, request, render_template
from google.cloud import vision
import requests
import json
import os
from PIL import Image, ImageDraw
import uuid
from threading import Timer
import time

app = Flask(__name__)
vision_client = vision.ImageAnnotatorClient()

UNKNOWN_FILE = "unknown_items.json"

def load_user_products():
    if os.path.exists("user_products.json"):
        with open("user_products.json", "r") as f:
            return json.load(f)
    return {}

def save_unknown_label(label):
    unknowns = []
    if os.path.exists("unknown_items.json"):
        with open("unknown_items.json", "r") as f:
            unknowns = json.load(f)

    if label not in unknowns:
        unknowns.append(label)
        with open("unknown_items.json", "w") as f:
            json.dump(unknowns, f, indent=2)

def get_product_info(label):
    # Check user-added products first
    user_products = load_user_products()
    if label in user_products:
        return user_products[label]

    # If not found, query DummyJSON
    response = requests.get(f'https://dummyjson.com/products/search?q={label}')
    if response.status_code == 200:
        data = response.json()
        if data['products']:
            product = data['products'][0]
            return {
                'title': product.get('title', 'Unknown'),
                'price': f"${product.get('price', 'N/A')}",
                'description': product.get('description', 'No description available.')
            }

    # If still not found, save to unknowns
    save_unknown_label(label)
    return {
        'title': 'Unknown',
        'price': 'N/A',
        'description': 'No product match found.'
    }

@app.route("/", methods=["GET"])
def home():
    return render_template("upload.html")

@app.route("/analyze", methods=["POST"])
def analyze():
    image_file = request.files['image']

    # Save original image
    img_id = str(uuid.uuid4())
    input_path = f"uploads/{img_id}.jpg"
    image_file.save(input_path)

    with open(input_path, "rb") as f:
        content = f.read()

    image = vision.Image(content=content)
    response = vision_client.object_localization(image=image)

    objects = response.localized_object_annotations

    # Draw boxes on image
    image_pil = Image.open(input_path).convert("RGB")
    draw = ImageDraw.Draw(image_pil)

    for obj in objects:
        box = [(vertex.x * image_pil.width, vertex.y * image_pil.height)
               for vertex in obj.bounding_poly.normalized_vertices]
        draw.line(box + [box[0]], width=3, fill="red")

    # Save processed image
    output_path = f"static/processed/{img_id}.jpg"
    image_pil.save(output_path)

    # Now retrieve product info using label names
    detected_items = []
    any_unknowns = False

    for obj in objects[:5]:
        label_text = obj.name
        product_info = get_product_info(label_text)

        if product_info["title"] == "Unknown":
            any_unknowns = True

        detected_items.append({
            "label": label_text,
            "title": product_info["title"],
            "price": product_info["price"],
            "description": product_info["description"]
        })

    # Render the results page first
    rendered_page = render_template("results.html", items=detected_items,
                                    any_unknowns=any_unknowns,
                                    annotated_image=output_path)

    # Cleanup after rendering
    try:
        os.remove(input_path)
    except Exception as e:
        print(f"Warning: Failed to delete original uploaded image: {e}")

    def delayed_delete(path):
        try:
            if os.path.exists(path):
                os.remove(path)
                print(f"Deleted: {path}")
        except Exception as e:
            print(f"Error deleting {path}: {e}")

    Timer(900, delayed_delete, args=(output_path,)).start()

    # Return results
    return render_template("results.html", items=detected_items,
                           any_unknowns=any_unknowns,
                           annotated_image=output_path)


    return rendered_page



@app.route("/label", methods=["GET", "POST"])
def label_unknowns():
    if request.method == "POST":
        label = request.form["label"]
        title = request.form["title"]
        price = request.form["price"]
        description = request.form["description"]

        # Save to user products
        user_products = load_user_products()
        user_products[label] = {
            "title": title,
            "price": price,
            "description": description
        }
        with open("user_products.json", "w") as f:
            json.dump(user_products, f, indent=2)

        # Remove from unknown list
        if os.path.exists("unknown_items.json"):
            with open("unknown_items.json", "r") as f:
                unknowns = json.load(f)
            unknowns = [item for item in unknowns if item != label]
            with open("unknown_items.json", "w") as f:
                json.dump(unknowns, f, indent=2)

        return render_template("label_success.html", label=label)

    # GET: Show list of unknowns
    unknowns = []
    if os.path.exists("unknown_items.json"):
        with open("unknown_items.json", "r") as f:
            unknowns = json.load(f)

    return render_template("label_form.html", unknowns=unknowns)

@app.route("/known")
def known_items():
    items = []

    if os.path.exists("user_products.json"):
        with open("user_products.json", "r") as f:
            products = json.load(f)
            for label, data in products.items():
                items.append({
                    "label": label,
                    "title": data.get("title", "N/A"),
                    "price": data.get("price", "N/A"),
                    "description": data.get("description", "N/A")
                })

    return render_template("known_items.html", items=items)


if __name__ == "__main__":
    import threading
    import webbrowser

    def open_browser():
        webbrowser.open_new("http://127.0.0.1:5000")

    # Only open browser on the initial run, not the Flask reloader
    if os.environ.get("WERKZEUG_RUN_MAIN") == "true":
        threading.Timer(1.5, open_browser).start()

    app.run(debug=True)
