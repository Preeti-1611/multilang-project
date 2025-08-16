import tkinter as tk
from tkinter import messagebox, ttk
import speech_recognition as sr
import time
from googletrans import Translator
from gtts import gTTS
from playsound import playsound
import os

# Professional color scheme
BG_COLOR = "#f5f7fa"  # Light gray background
PRIMARY_COLOR = "#3498db"  # Professional blue
SECONDARY_COLOR = "#2c3e50"  # Dark blue/slate for text
ACCENT_COLOR = "#e74c3c"  # Accent red for important elements
BUTTON_HOVER = "#2980b9"  # Slightly darker blue for hover states

root = tk.Tk()
root.title("Multilangual Speech Recognition")
root.geometry("500x400")
root.configure(bg=BG_COLOR)  # Set background color

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
        record_btn.config(text="Stop Recording", bg=ACCENT_COLOR)
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
                record_btn.config(text="Start Recording", bg=PRIMARY_COLOR)
                return
        recording = False
        record_btn.config(text="Start Recording", bg=PRIMARY_COLOR)
        show_language_selection()
    else:
        recording = False
        record_btn.config(text="Start Recording", bg=PRIMARY_COLOR)

# Show language selection dropdown
def show_language_selection():
    lang_window = tk.Toplevel(root)
    lang_window.title("Select Target Language")
    lang_window.geometry("350x200")
    lang_window.configure(bg=BG_COLOR)
    
    # Add a header frame
    header_frame = tk.Frame(lang_window, bg=PRIMARY_COLOR, height=40)
    header_frame.pack(fill="x")
    tk.Label(header_frame, text="Select Translation Language", font=("Arial", 14, "bold"), 
             bg=PRIMARY_COLOR, fg="white").pack(pady=8)
    
    # Content frame
    content_frame = tk.Frame(lang_window, bg=BG_COLOR)
    content_frame.pack(fill="both", expand=True, padx=20, pady=20)
    
    tk.Label(content_frame, text="Select language to translate to:", 
             font=("Arial", 12), bg=BG_COLOR, fg=SECONDARY_COLOR).pack(pady=10)
    
    lang_var = tk.StringVar(value="English")
    style = ttk.Style()
    style.configure("TCombobox", fieldbackground=BG_COLOR, background=PRIMARY_COLOR)
    
    lang_menu = ttk.Combobox(content_frame, textvariable=lang_var, 
                            values=list(LANGUAGES.keys()), 
                            state="readonly", font=("Arial", 12), width=20)
    lang_menu.pack(pady=10)
    
    def on_select():
        lang_window.destroy()
        recognize_and_prepare_translation(LANGUAGES[lang_var.get()])
    
    translate_btn = tk.Button(content_frame, text="Translate & Speak", 
                             command=on_select, font=("Arial", 12, "bold"),
                             bg=PRIMARY_COLOR, fg="white", 
                             activebackground=BUTTON_HOVER,
                             activeforeground="white", 
                             relief=tk.FLAT, padx=15, pady=8)
    translate_btn.pack(pady=10)

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

# Create a header frame
header_frame = tk.Frame(root, bg=PRIMARY_COLOR, height=60)
header_frame.pack(fill="x")

# Add a title to the header
title_label = tk.Label(header_frame, text="Multilingual Speech Translator", 
                      font=("Arial", 16, "bold"), bg=PRIMARY_COLOR, fg="white")
title_label.pack(pady=15)

# Create a main content frame
content_frame = tk.Frame(root, bg=BG_COLOR)
content_frame.pack(fill="both", expand=True, padx=20, pady=20)

# Add Start/Stop Recording button with styling
record_btn = tk.Button(content_frame, text="Start Recording", 
                      command=toggle_recording, font=("Arial", 14, "bold"),
                      bg=PRIMARY_COLOR, fg="white", 
                      activebackground=BUTTON_HOVER,
                      activeforeground="white", 
                      relief=tk.FLAT, padx=20, pady=10)
record_btn.pack(pady=30)

# Add a styled frame for the text display
text_frame = tk.Frame(content_frame, bg="white", 
                     highlightbackground=PRIMARY_COLOR, 
                     highlightthickness=1, padx=10, pady=10)
text_frame.pack(fill="x", padx=20, pady=10)

# Add a label to display recognized text with improved styling
recognized_text_var = tk.StringVar()
recognized_text_label = tk.Label(text_frame, textvariable=recognized_text_var, 
                               font=("Arial", 12), bg="white", fg=SECONDARY_COLOR,
                               wraplength=400, justify="center")
recognized_text_label.pack(pady=10, fill="x")

# Add a footer with version info
footer_frame = tk.Frame(root, bg=BG_COLOR)
footer_frame.pack(fill="x", side="bottom")
tk.Label(footer_frame, text="© 2023 BhashaVaani - v1.0", 
        font=("Arial", 8), bg=BG_COLOR, fg=SECONDARY_COLOR).pack(pady=5)

root.mainloop()