# utils/annotator.py

import whisper
from pyannote.audio import Pipeline
from datetime import timedelta

def diarize_and_transcribe(audio_file_path):
    print(f"🎧 Loading audio from: {audio_file_path}")
    
    # 🔤 Load Whisper
    print("🔤 Loading Whisper model...")
    model = whisper.load_model("base")

    print("📝 Transcribing with Whisper...")
    result = model.transcribe(audio_file_path, word_timestamps=True)

    print("🔊 Loading PyAnnote diarization pipeline...")
    pipeline = Pipeline.from_pretrained("pyannote/speaker-diarization")

    print("🧠 Performing speaker diarization...")
    diarization = pipeline(audio_file_path)

    print("📎 Aligning transcription with speakers...")
    annotated = []

    for turn, _, speaker in diarization.itertracks(yield_label=True):
        speaker_text = ""
        for segment in result["segments"]:
            if segment["start"] >= turn.start and segment["end"] <= turn.end:
                speaker_text += segment["text"].strip() + " "
        if speaker_text.strip():
            start = str(timedelta(seconds=int(turn.start)))
            end = str(timedelta(seconds=int(turn.end)))
            annotated.append(f"[{speaker}] ({start} - {end}) {speaker_text.strip()}")

    # 💾 Save to text file
    transcript_path = audio_file_path.replace(".wav", "_annotated.txt")
    with open(transcript_path, "w") as f:
        for line in annotated:
            f.write(line + "\n")

    print(f"✅ Annotated transcript saved to: {transcript_path}")
