import os
from flask import Flask, request, jsonify, send_file, session
from flask_cors import CORS
import requests
import logging
import io

app = Flask(__name__)
app.secret_key = os.urandom(24)  # Replace with your actual secret key
CORS(app)  # Enable CORS for all routes

# Configure logging
logging.basicConfig(level=logging.DEBUG)

# Google Cloud model URL for text generation (replace with actual URL)
GOOGLE_CLOUD_MODEL_URL = "https://29f9-35-187-235-204.ngrok-free.app/generate"

# Play.ht API configuration (replace with your actual API key and any secure storage)
PLAYHT_API_URL = "https://api.play.ht/api/v2/tts/stream"
PLAYHT_HEADERS = {
    "accept": "audio/mpeg",
    "content-type": "application/json",
    "Authorization": "Bearer YOUR_PLAYHT_API_KEY"
}

@app.route('/generate', methods=['POST'])
def generate():
    """Route for generating text via Google Cloud model."""
    data = request.get_json()
    if not data or 'prompt' not in data:
        return jsonify({'error': 'Invalid request, "prompt" field is required'}), 400
    
    prompt = data['prompt']
    logging.debug(f"Received prompt: {prompt}")

    # Initialize conversation history if not present
    if 'conversation_history' not in session:
        session['conversation_history'] = []

    # Append the user's prompt to the conversation history
    session['conversation_history'].append({'role': 'user', 'content': prompt})

    # Prepare the conversation history for the model
    conversation_history = session['conversation_history']

    try:
        # Forward the conversation history to the Google Cloud model
        response = requests.post(GOOGLE_CLOUD_MODEL_URL, json={'conversation': conversation_history})
        
        # Log and handle the response from the Google Cloud model
        logging.debug(f"Google Cloud model response status: {response.status_code}")
        response.raise_for_status()  # Raise error for HTTP errors
        response_data = response.json()
        logging.debug(f"Google Cloud model response content: {response_data}")

        # Console log the entire JSON response for debugging
        print("Google Cloud model response JSON:", response_data)

        # Extract the generated text from the response
        generated_text_list = response_data.get('generated_text', [])
        if not generated_text_list:
            logging.error(f"Unexpected response format: {response_data}")
            return jsonify({'error': 'Unexpected response format'}), 500

        # Extract the content of the last response from the assistant
        generated_text = generated_text_list[-1].get('content', '')

        # Append the model's response to the conversation history
        session['conversation_history'].append({'role': 'model', 'content': generated_text})

        return jsonify({'text': generated_text})

    except requests.exceptions.RequestException as e:
        logging.error(f"Google Cloud model request error: {e}")
        return jsonify({'error': 'Failed to fetch response from Google Cloud model'}), 500

    except Exception as e:
        logging.error(f"An error occurred: {e}")
        return jsonify({'error': 'An internal error occurred'}), 500

@app.route('/generate-audio-playht', methods=['POST'])
def generate_audio_playht():
    try:
        data = request.get_json()
        text = data.get('text', '')
        voice = data.get('voice', 's3://voice-cloning-zero-shot/d9ff78ba-d016-47f6-b0ef-dd630f59414e/female-cs/manifest.json')  # Default voice
        audio_format = data.get('audioFormat', 'mp3')  # Default audio format

        # Log the request payload
        logging.debug(f"Request payload: {data}")

        # Make a request to the Play.ht API
        payload = {
            "voice": voice,
            "output_format": audio_format,
            "text": text
        }
        response = requests.post(PLAYHT_API_URL, headers=PLAYHT_HEADERS, json=payload)
        
        # Log the response status and content
        logging.debug(f"Play.ht API response status: {response.status_code}")
        response.raise_for_status()  # Raise error for HTTP errors

        audio_data = response.content
        return send_file(
            io.BytesIO(audio_data),
            mimetype=f"audio/{audio_format}",
            as_attachment=True,
            download_name=f"audio.{audio_format}"
        )

    except requests.exceptions.RequestException as e:
        logging.error(f"Play.ht request error: {e}")
        return jsonify({'error': 'Failed to generate audio'}), 500

    except Exception as e:
        logging.error(f"Audio generation error: {e}")
        return jsonify({'error': 'An internal error occurred'}), 500

if __name__ == '__main__':
    app.run(host='0.0.0.0', port=5001)