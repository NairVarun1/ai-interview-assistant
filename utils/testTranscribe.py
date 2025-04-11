import whisper

model = whisper.load_model("base")
result = model.transcribe("recordings/meeting_audio_20250411_131716.wav")
print("📝 Transcript:", result["text"])
