import os
import google.generativeai as genai
from flask import Flask, render_template, request, session, jsonify, send_from_directory
from flask_session import Session
from werkzeug.utils import secure_filename
from PIL import Image
import pytesseract
import speech_recognition as sr
from pydub import AudioSegment
import markdown
from datetime import datetime

# Flask app configuration
app = Flask(__name__)
app.secret_key = "secret_key_for_sessions"  # Change this in production
app.config["SESSION_TYPE"] = "filesystem"
app.config["UPLOAD_FOLDER"] = "uploads"
app.config["ALLOWED_EXTENSIONS"] = {"png", "jpg", "jpeg", "mp3", "wav", "txt"}
Session(app)

# Ensure the upload folder exists
os.makedirs(app.config["UPLOAD_FOLDER"], exist_ok=True)

# Configure the Gemini model
genai.configure(api_key=os.getenv("GEMINI_API_KEY"))
model = genai.GenerativeModel("gemini-1.5-flash")

# Constant to limit the interaction history
MAX_HISTORY = 4

# Set the Tesseract path explicitly if needed
pytesseract.pytesseract.tesseract_cmd = r"C:\\Program Files\\Tesseract-OCR\\tesseract.exe"

def allowed_file(filename):
    """Check if a file is allowed based on its extension."""
    return "." in filename and filename.rsplit(".", 1)[1].lower() in app.config["ALLOWED_EXTENSIONS"]

def process_file(file_path, file_type):
    """Extract content or metadata from the uploaded file."""
    if file_type in {"png", "jpg", "jpeg"}:
        text = pytesseract.image_to_string(Image.open(file_path))
        return text or "No text found in the image."
    elif file_type in {"mp3", "wav"}:
        if not file_path.endswith(".wav"):
            audio = AudioSegment.from_file(file_path)
            file_path = os.path.splitext(file_path)[0] + ".wav"
            audio.export(file_path, format="wav")
        recognizer = sr.Recognizer()
        try:
            with sr.AudioFile(file_path) as source:
                audio = recognizer.record(source)
                text = recognizer.recognize_google(audio)
                return text
        except sr.UnknownValueError:
            return "Audio was not clear enough to extract text."
        except sr.RequestError:
            return "Error in the speech recognition service."
    elif file_type == "txt":
        with open(file_path, "r") as file:
            return file.read()
    return "Unsupported file type."

@app.route("/")
def index():
    if "history" not in session:
        session["history"] = []
    return render_template("index.html", history=session["history"])

@app.route("/predict", methods=["POST"])
def predict():
    history = session.get("history", [])
    uploaded_file = request.files.get("file")
    file_content = ""
    file_name = ""

    if uploaded_file and allowed_file(uploaded_file.filename):
        file_name = secure_filename(uploaded_file.filename)
        file_path = os.path.join(app.config["UPLOAD_FOLDER"], file_name)
        uploaded_file.save(file_path)
        file_type = file_name.rsplit(".", 1)[1].lower()
        file_content = process_file(file_path, file_type)

    prompt = request.form.get("prompt", "")
    combined_input = f"<b>Uploaded file:</b> {file_name}\n{file_content}\n\n<b>User Input:</b> {prompt}".strip()

    try:
        response = model.generate_content(combined_input).text
        output_html = markdown.markdown(response)
        now=datetime.now()
        formatted_datetime=now.strftime("%Y-%m-%d %H:%M:%S")
        history.append({
            "prompt": combined_input,
            "response_raw": response,
            "response_html": output_html,
            "created_at": formatted_datetime
        })
        session["history"] = history
        return jsonify({"prompt": combined_input, "response_html": output_html})
    except Exception as e:
        return jsonify({"error": f"Error: {e}"})

@app.route("/view-history/<int:index>", methods=["GET"])
def view_history(index):
    history = session.get("history", [])
    if 0 <= index < len(history):
        return jsonify(history[index])
    return jsonify({"error": "Invalid index."}), 400

@app.route("/edit-history/<int:index>", methods=["POST"])
def edit_history(index):
    history = session.get("history", [])
    if 0 <= index < len(history):
        data = request.json
        new_prompt = data.get("prompt")
        if new_prompt:
            history[index]["prompt"] = new_prompt
            session["history"] = history
            return jsonify({"success": True})
    return jsonify({"error": "Invalid index or missing prompt."}), 400

@app.route("/delete-history/<int:index>", methods=["POST"])
def delete_history(index):
    history = session.get("history", [])
    if 0 <= index < len(history):
        history.pop(index)
        session["history"] = history
        return jsonify({"success": True})
    return jsonify({"error": "Invalid index."}), 400

if __name__ == "__main__":
    app.run(debug=True)
