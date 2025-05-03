# Cloud Vision Object Labeling App

This Flask app lets users upload an image, detects objects using the Google Vision API, draws bounding boxes with confidence scores, and lets users label unknown items manually.

## 🔧 Setup Instructions

1. Clone the repository:


2. Create and activate a virtual environment:

```bash
python -m venv venv
venv\Scripts\activate     # Windows
# or
source venv/bin/activate  # macOS/Linux

pip install -r requirements.txt

$env:GOOGLE_APPLICATION_CREDENTIALS="C:\full\path\to\your\credentials.json"  # Windows
# or
export GOOGLE_APPLICATION_CREDENTIALS="/full/path/to/your/credentials.json"  # macOS/Linux

python app.py
