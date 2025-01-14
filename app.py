import os
from flask import Flask, render_template, request, redirect, url_for, jsonify
import requests

app = Flask(__name__)
app.config['UPLOAD_FOLDER'] = 'static/uploads'
app.config['MAX_CONTENT_LENGTH'] = 16 * 1024 * 1024  # Max upload size: 16 MB

# Hugging Face API Configuration
API_URL = "https://api-inference.huggingface.co/models/Salesforce/blip-image-captioning-base"
HEADERS = {"Authorization": "Bearer ##############"}


def query_image_caption(filename):
    """Send image to Hugging Face API and return the generated caption."""
    with open(filename, "rb") as file:
        response = requests.post(API_URL, headers=HEADERS, data=file.read())

    if response.status_code == 200:
        try:
            response_data = response.json()
            # Debugging: Print the API response
            print("API Response:", response_data)

            # Check if the response is a list or a dictionary
            if isinstance(response_data, dict):
                return response_data.get("generated_text", "No caption generated.")
            elif isinstance(response_data, list) and len(response_data) > 0:
                return response_data[0].get("generated_text", "No caption generated.")
        except Exception as e:
            print(f"Error parsing response: {e}")
            return "Error parsing API response."

    # Handle non-200 responses
    print(f"API Error: {response.status_code}, {response.text}")
    return "Error generating caption."

# Routes
@app.route('/')
def index():
    """Homepage displaying uploaded albums."""
    albums = os.listdir(app.config['UPLOAD_FOLDER'])
    return render_template('index.html', albums=albums)


@app.route('/upload', methods=['GET', 'POST'])
def upload_image():
    """Handle image uploads."""
    if request.method == 'POST':
        files = request.files.getlist('images')
        album = request.form.get('album', 'default')
        album_folder = os.path.join(app.config['UPLOAD_FOLDER'], album)
        os.makedirs(album_folder, exist_ok=True)
        captions = {}

        for file in files:
            if file:
                file_path = os.path.join(album_folder, file.filename)
                file.save(file_path)

                # Generate caption
                caption = query_image_caption(file_path)
                captions[file.filename] = caption

        return jsonify(captions)  # Return captions for uploaded images
    return render_template('upload.html')


@app.route('/album/<album_name>')
def view_album(album_name):
    """Display images in the album with captions."""
    album_folder = os.path.join(app.config['UPLOAD_FOLDER'], album_name)
    images = os.listdir(album_folder)
    image_captions = {}

    for image in images:
        image_path = os.path.join(album_folder, image)
        caption = query_image_caption(image_path)
        image_captions[image] = caption

    return render_template('album.html', album_name=album_name, images=image_captions)


if __name__ == '__main__':
    app.run(debug=True)
