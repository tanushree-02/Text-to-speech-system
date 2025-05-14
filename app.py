from flask import Flask, render_template, request, jsonify, send_file
import pyttsx3
import os
import uuid
from io import BytesIO
from flask_cors import CORS 

app = Flask(__name__)
CORS(app)  # Enable CORS for all routes

# Configure upload folder
UPLOAD_FOLDER = 'temp_audio'
os.makedirs(UPLOAD_FOLDER, exist_ok=True)

@app.route('/')
def index():
    return render_template('index.html')

@app.route('/convert', methods=['POST'])
def convert_text_to_speech():
    try:
        text = request.form.get('text', '')
        voice_type = request.form.get('voice', 'female')
        rate = int(request.form.get('rate', 150))
        
        if not text.strip():
            return jsonify({'error': 'Please enter some text to convert'}), 400
        
        # Initialize the TTS engine with error handling
        try:
            engine = pyttsx3.init()
        except Exception as init_error:
            app.logger.error(f"pyttsx3 initialization failed: {str(init_error)}")
            return jsonify({'error': 'TTS engine initialization failed'}), 500
        
        # Set properties
        engine.setProperty('rate', rate)
        
        # Voice selection with better error handling
        try:
            voices = engine.getProperty('voices')
            if voice_type == 'male':
                if len(voices) > 0:
                    engine.setProperty('voice', voices[0].id)
                else:
                    return jsonify({'error': 'No male voice available'}), 400
            else:
                if len(voices) > 1:
                    engine.setProperty('voice', voices[1].id)
                else:
                    return jsonify({'error': 'No female voice available'}), 400
        except Exception as voice_error:
            app.logger.error(f"Voice selection failed: {str(voice_error)}")
            return jsonify({'error': 'Voice selection failed'}), 500
        
        # Generate unique filename
        filename = f"speech_{uuid.uuid4().hex}.mp3"
        filepath = os.path.join(UPLOAD_FOLDER, filename)
        
        try:
            # Save to file
            engine.save_to_file(text, filepath)
            engine.runAndWait()
            
            # Verify file was created
            if not os.path.exists(filepath):
                return jsonify({'error': 'Audio file was not generated'}), 500
                
            # Get file size
            file_size = os.path.getsize(filepath)
            if file_size == 0:
                return jsonify({'error': 'Empty audio file generated'}), 500
                
            # Return the audio file
            return send_file(
                filepath,
                as_attachment=True,
                download_name="speech_output.mp3",
                mimetype="audio/mpeg"
            )
            
        except Exception as conversion_error:
            app.logger.error(f"Conversion failed: {str(conversion_error)}")
            return jsonify({'error': 'Audio conversion failed'}), 500
            
    except Exception as e:
        app.logger.error(f"Unexpected error: {str(e)}")
        return jsonify({'error': 'An unexpected error occurred'}), 500

if __name__ == '__main__':
    app.run(debug=True)