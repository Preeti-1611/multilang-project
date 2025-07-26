from flask import Flask, render_template, request, jsonify, send_file, session, make_response
import os
import tempfile
import speech_recognition as sr
from googletrans import Translator
from gtts import gTTS
from pydub import AudioSegment
import uuid

from datetime import datetime

app = Flask(__name__)
app.secret_key = "your_secret_key"  # Needed for session
app.config['TEMPLATES_AUTO_RELOAD'] = True
app.config['SEND_FILE_MAX_AGE_DEFAULT'] = 0

def smart_punctuate(text):
    text = text.strip()
    if not text:
        return text
    if text[-1] in '.!?':
        return text
    # Simple heuristic: if it starts with a question word, add '?'
    question_words = ['who', 'what', 'when', 'where', 'why', 'how', 'is', 'are', 'do', 'does', 'did', 'can', 'could', 'will', 'would', 'should']
    if any(text.lower().startswith(qw + ' ') for qw in question_words):
        return text + '?'
    return text + '.'

def to_bullet_points(text):
    # Split by commas for simple lists
    items = [item.strip() for item in text.split(',') if item.strip()]
    if len(items) > 1:
        return '\n'.join(f'• {item}' for item in items)
    return text

@app.route('/')
def index():
    response = make_response(render_template('index.html'))
    response.headers['Cache-Control'] = 'no-cache, no-store, must-revalidate'
    response.headers['Pragma'] = 'no-cache'
    response.headers['Expires'] = '0'
    return response

@app.route('/process', methods=['POST'])
def process():
    audio_file = request.files['audio']
    output_lang = request.form['output_lang']
    temp_dir = tempfile.gettempdir()
    raw_path = os.path.join(temp_dir, 'input.webm')
    wav_path = os.path.join(temp_dir, 'input.wav')
    audio_file.save(raw_path)

    try:
        audio = AudioSegment.from_file(raw_path, format="webm")
        audio.export(wav_path, format='wav')
    except Exception as e:
        print(f"Audio conversion failed: {e}")
        return jsonify({'recognized': f'Error converting audio: {e}', 'translated': '', 'audio_file': None})

    recognizer = sr.Recognizer()
    input_lang = request.form.get('input_lang', 'en-US')
    SUPPORTED_INPUT_LANGS = ['en-US', 'hi-IN', 'kn-IN', 'mr-IN']
    SUPPORTED_OUTPUT_LANGS = ['en', 'hi', 'kn', 'mr']

    if input_lang not in SUPPORTED_INPUT_LANGS or output_lang not in SUPPORTED_OUTPUT_LANGS:
        return jsonify({'recognized': '', 'translated': '', 'audio_file': None, 'error': 'Unsupported language selected.'})

    try:
        with sr.AudioFile(wav_path) as source:
            audio = recognizer.record(source)
        recognized = recognizer.recognize_google(audio, language=input_lang)
        recognized = smart_punctuate(recognized)
        recognized = to_bullet_points(recognized)
    except Exception as e:
        print(f"Speech recognition failed: {e}")
        not_recognized_text = "Not recognized"
        try:
            translator = Translator()
            translated = translator.translate(not_recognized_text, dest=output_lang).text
            tts_filename = f"not_recognized_{uuid.uuid4().hex}.mp3"
            tts_path = os.path.join(temp_dir, tts_filename)
            tts = gTTS(translated, lang=output_lang)
            tts.save(tts_path)
            return jsonify({'recognized': not_recognized_text, 'translated': translated, 'audio_file': tts_filename})
        except Exception as tts_e:
            return jsonify({'recognized': not_recognized_text, 'translated': '', 'audio_file': None})

    translator = Translator()
    try:
        translated = translator.translate(recognized, dest=output_lang).text
    except Exception as e:
        print(f"Translation failed: {e}")
        return jsonify({'recognized': recognized, 'translated': f"Error translating: {e}", 'audio_file': None})

    try:
        tts_filename = f"output_{uuid.uuid4().hex}.mp3"
        tts_path = os.path.join(temp_dir, tts_filename)
        tts = gTTS(translated, lang=output_lang)
        tts.save(tts_path)
    except Exception as e:
        print(f"TTS failed: {e}")
        return jsonify({'recognized': recognized, 'translated': translated, 'audio_file': None})

    history_item = {
        'recognized': recognized,
        'translated': translated,
        'audio_file': tts_filename,
        'timestamp': datetime.now().isoformat()
    }
    if 'history' not in session:
        session['history'] = []
    session['history'].append(history_item)
    session.modified = True

    return jsonify({
        'recognized': recognized,
        'translated': translated,
        'audio_file': tts_filename
    })

@app.route('/audio/<filename>')
def audio(filename):
    temp_dir = tempfile.gettempdir()
    tts_path = os.path.join(temp_dir, filename)
    if tts_path and os.path.exists(tts_path):
        return send_file(tts_path, mimetype='audio/mpeg')
    return '', 404



@app.route('/history', methods=['GET'])
def get_history():
    return jsonify(session.get('history', []))

@app.route('/history/clear', methods=['POST'])
def clear_history():
    session['history'] = []
    session.modified = True
    return jsonify({'status': 'cleared'})

@app.route('/history/delete', methods=['POST'])
def delete_history_item():
    data = request.get_json()
    timestamp = data.get('timestamp')
    if not timestamp:
        return jsonify({'error': 'No timestamp provided'}), 400

    history = session.get('history', [])
    new_history = [item for item in history if item.get('timestamp') != timestamp]
    session['history'] = new_history
    session.modified = True
    return jsonify({'status': 'deleted'})

@app.route('/sw.js')
def service_worker():
    return send_file('static/sw.js', mimetype='application/javascript')

if __name__ == '__main__':
    app.run(debug=True)
