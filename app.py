import os
from flask import Flask, request, send_file, jsonify, render_template
from flask import redirect, url_for
from nudenet import NudeDetector
from PIL import Image, ImageDraw, ImageFont
from datetime import datetime
import uuid

app = Flask(__name__)
app.config['UPLOAD_FOLDER'] = 'uploads'
app.config['RESULT_FOLDER'] = 'results'

# Ensure upload and result folders exist
os.makedirs(app.config['UPLOAD_FOLDER'], exist_ok=True)
os.makedirs(app.config['RESULT_FOLDER'], exist_ok=True)

# Load NudeNet's NudeDetector model
detector = NudeDetector()

# Define label categories and color mapping
all_labels = {
    "FEMALE_GENITALIA_COVERED": "purple",
    "FACE_FEMALE": "red",
    "BUTTOCKS_EXPOSED": "orange",
    "FEMALE_BREAST_EXPOSED": "pink",
    "FEMALE_GENITALIA_EXPOSED": "purple",
    "MALE_BREAST_EXPOSED": "green",
    "ANUS_EXPOSED": "brown",
    "FEET_EXPOSED": "yellow",
    "BELLY_COVERED": "pink",
    "FEET_COVERED": "yellow",
    "ARMPITS_COVERED": "gray",
    "ARMPITS_EXPOSED": "gray",
    "FACE_MALE": "blue",
    "BELLY_EXPOSED": "pink",
    "MALE_GENITALIA_EXPOSED": "purple",
    "ANUS_COVERED": "brown",
    "FEMALE_BREAST_COVERED": "pink",
    "BUTTOCKS_COVERED": "orange",
}

@app.route('/')
def index():
    return render_template("index.html")

@app.route('/results', methods=['GET'])
def list_results():
    result_files = [
        f for f in os.listdir(app.config['RESULT_FOLDER'])
        if os.path.isfile(os.path.join(app.config['RESULT_FOLDER'], f))
    ]
    return render_template("results.html", result_files=result_files)

@app.route('/detect', methods=['POST'])
def detect_nudity():
    if 'image' not in request.files:
        return "No file uploaded", 400

    file = request.files['image']
    if file.filename == '':
        return "No selected file", 400

    # Generate a unique file name with a timestamp and UUID
    timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')
    unique_id = uuid.uuid4().hex
    file_extension = os.path.splitext(file.filename)[1]
    unique_filename = f"{timestamp}_{unique_id}{file_extension}"
    image_path = os.path.join(app.config['UPLOAD_FOLDER'], unique_filename)
    file.save(image_path)

    # Use NudeNet to detect nudity
    results = detector.detect(image_path)

    # Load the image and prepare for drawing
    image = Image.open(image_path).convert("RGB")
    draw = ImageDraw.Draw(image)

    # Load the font
    try:
        font = ImageFont.truetype("arial.ttf", 40)
    except IOError:
        font = ImageFont.load_default()
    used_positions = []

    def check_overlap(position, width, height):
        for used_x0, used_y0, used_x1, used_y1 in used_positions:
            if (used_x0 < position[0] + width and used_x1 > position[0] and
                used_y0 < position[1] + height and used_y1 > position[1]):
                return True
        return False

    if isinstance(results, list):
        for result in results:
            if isinstance(result, dict):
                label = result['class']
                score = result['score']
                box = result['box']
                color = all_labels.get(label, "black")

                if label in all_labels:
                    x0, y0, w, h = box
                    x1, y1 = x0 + w, y0 + h

                    draw.rectangle([x0, y0, x1, y1], outline=color, width=3)
                    label_text = f"{label}"
                    label_bbox = draw.textbbox((0, 0), label_text, font=font)
                    text_width = label_bbox[2] - label_bbox[0]
                    text_height = label_bbox[3] - label_bbox[1]
                    label_position = (x0 + (w - text_width) // 2, max(0, y0 - text_height - 10))
                    while check_overlap(label_position, text_width, text_height):
                        label_position = (label_position[0], label_position[1] - text_height - 10)
                    draw.text(label_position, label_text, fill=color, font=font)
                    used_positions.append((label_position[0], label_position[1], 
                                           label_position[0] + text_width, label_position[1] + text_height))

                    confidence_text = f"{score:.2f}"
                    confidence_bbox = draw.textbbox((0, 0), confidence_text, font=font)
                    text_width = confidence_bbox[2] - confidence_bbox[0]
                    text_height = confidence_bbox[3] - confidence_bbox[1]
                    confidence_position = (x0 + (w - text_width) // 2, y1 + 10)
                    while check_overlap(confidence_position, text_width, text_height):
                        confidence_position = (confidence_position[0], confidence_position[1] + text_height + 10)
                    draw.text(confidence_position, confidence_text, fill=color, font=font)
                    used_positions.append((confidence_position[0], confidence_position[1], 
                                           confidence_position[0] + text_width, confidence_position[1] + text_height))

    result_path = os.path.join(app.config['RESULT_FOLDER'], 'result_' + unique_filename)
    image.save(result_path)
    return send_file(result_path, mimetype='image/jpeg')

@app.route('/result/<filename>')
def get_result(filename):
    """Provide access to a single result image"""
    result_path = os.path.join(app.config['RESULT_FOLDER'], filename)
    if os.path.exists(result_path):
        return send_file(result_path, mimetype='image/jpeg')
    else:
        return "File not found", 404



@app.route('/delete/<filename>', methods=['POST'])
def delete_result(filename):
    result_path = os.path.join(app.config['RESULT_FOLDER'], filename)
    if os.path.exists(result_path):
        os.remove(result_path)
        # Redirect to the results page after deletion
        return redirect(url_for('list_results'))
    else:
        # Return a message if the file doesn't exist
        return jsonify({"message": "File not found"}), 404


if __name__ == '__main__':
    app.run(debug=False)