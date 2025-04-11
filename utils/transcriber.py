# utils/transcriber.py
import whisper
import os

def transcribe_audio(filepath):
    print("🔍 Transcribing audio...")
    model = whisper.load_model("base")
    result = model.transcribe(filepath)
    text = result["text"]

    # Save to .txt file
    text_filename = filepath.replace(".wav", ".txt")
    with open(text_filename, "w") as f:
        f.write(text)

    print(f"📝 Transcription saved to: {text_filename}")
    return text
