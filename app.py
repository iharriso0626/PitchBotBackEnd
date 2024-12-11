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
GOOGLE_CLOUD_MODEL_URL = "https://18df-35-240-225-50.ngrok-free.app/generate"

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

    # Retrieve conversation history from session
    conversation_history = session.get('conversation_history', [])

    # Add the new user message to the conversation history
    user_message = data['prompt']
    conversation_history.append({'role': 'user', 'content': user_message})

    # Prepare the payload for the model
    payload = {
        'messages': conversation_history
    }

    try:
        # Make a request to the Google Cloud model
        response = requests.post(GOOGLE_CLOUD_MODEL_URL, json=payload)
        response.raise_for_status()  # Raise error for HTTP errors

        # Get the model's response
        model_response = response.json()
        logging.debug(f"Model response: {model_response}")

        bot_message = model_response.get('choices', [{}])[0].get('message', {}).get('content', '')

        # Add the bot's response to the conversation history
        conversation_history.append({'role': 'bot', 'content': bot_message})

        # Save the updated conversation history in the session
        session['conversation_history'] = conversation_history

        return jsonify(model_response)


    except requests.exceptions.RequestException as e:
        logging.error(f"Request error: {e}")
        return jsonify({'error': 'Failed to generate response'}), 500

    except Exception as e:
        logging.error(f"Error: {e}")
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