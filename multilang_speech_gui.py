import tkinter as tk
from tkinter import messagebox, ttk
import speech_recognition as sr
import time
from googletrans import Translator
from gtts import gTTS
from playsound import playsound
import os

root = tk.Tk()
root.title("Multilangual Speech Recognition")
root.geometry("400x300")

recognizer = sr.Recognizer()
audio_data = None
recording = False

# Supported languages for translation
LANGUAGES = {
    "English": "en",
    "Hindi": "hi",
    "Kannada": "kn"
}

# Start/Stop recording logic

def toggle_recording():
    global recording, audio_data
    if not recording:
        record_btn.config(text="Stop Recording")
        root.update()
        with sr.Microphone() as source:
            messagebox.showinfo("Info", "Click 'Stop Recording' when you are done speaking.")
            recognizer.adjust_for_ambient_noise(source, duration=1)  # NEW: calibrate for noise
            recording = True
            try:
                audio_data = recognizer.listen(source, timeout=None, phrase_time_limit=None)
            except Exception as e:
                messagebox.showerror("Error", f"Error during recording: {e}")
                recording = False
                record_btn.config(text="Start Recording")
                return
        recording = False
        record_btn.config(text="Start Recording")
        show_language_selection()
    else:
        recording = False
        record_btn.config(text="Start Recording")

# Show language selection dropdown
def show_language_selection():
    lang_window = tk.Toplevel(root)
    lang_window.title("Select Target Language")
    lang_window.geometry("300x150")
    tk.Label(lang_window, text="Select language to translate to:", font=("Arial", 12)).pack(pady=10)
    lang_var = tk.StringVar(value="English")
    lang_menu = ttk.Combobox(lang_window, textvariable=lang_var, values=list(LANGUAGES.keys()), state="readonly", font=("Arial", 12))
    lang_menu.pack(pady=10)
    def on_select():
        lang_window.destroy()
        recognize_and_prepare_translation(LANGUAGES[lang_var.get()])
    tk.Button(lang_window, text="Translate & Speak", command=on_select, font=("Arial", 12)).pack(pady=10)

# Recognize speech and prepare for translation

def recognize_and_prepare_translation(target_lang_code):
    global audio_data
    try:
        text = recognizer.recognize_google(audio_data, language="en-US")
        recognized_text_var.set(f"Recognized: {text}")
        # Translate the text
        translator = Translator()
        translated = translator.translate(text, dest=target_lang_code)
        translated_text = translated.text
        # Show translated text in the main window
        recognized_text_var.set(f"Recognized: {text}\nTranslated: {translated_text}")
        # Speak the translated text
        tts = gTTS(translated_text, lang=target_lang_code)
        audio_file = "translated_audio.mp3"
        tts.save(audio_file)
        playsound(audio_file)
        os.remove(audio_file)
    except sr.UnknownValueError:
        recognized_text_var.set("")
        messagebox.showerror("Error", "Could not understand the audio.")
    except sr.RequestError as e:
        recognized_text_var.set("")
        messagebox.showerror("Error", f"Could not request results; {e}")
    except Exception as e:
        messagebox.showerror("Error", f"Translation or speech error: {e}")

# Add Start/Stop Recording button
record_btn = tk.Button(root, text="Start Recording", command=toggle_recording, font=("Arial", 16))
record_btn.pack(pady=60)

# Add a label to display recognized text
recognized_text_var = tk.StringVar()
recognized_text_label = tk.Label(root, textvariable=recognized_text_var, font=("Arial", 12), wraplength=350, justify="center")
recognized_text_label.pack(pady=10)

root.mainloop() 