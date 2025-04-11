# utils/transcriber.py
import whisper
import os

model = whisper.load_model("base")  # Load once and reuse

def transcribe_audio(audio_path, output_dir="transcripts"):
    os.makedirs(output_dir, exist_ok=True)

    print(f"🔍 Transcribing audio: {audio_path}")
    result = model.transcribe(audio_path)

    text = result["text"]
    transcript_filename = os.path.splitext(os.path.basename(audio_path))[0] + ".txt"
    transcript_path = os.path.join(output_dir, transcript_filename)

    with open(transcript_path, "w") as f:
        f.write(text)

    print(f"✅ Transcript saved to: {transcript_path}")
    return transcript_path
