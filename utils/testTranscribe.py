import whisper

# Load Whisper model
model = whisper.load_model("base")  # You can use "tiny", "base", "small", etc.

# Path to your recorded audio

audio_path = "sample_interview/interview_with_two_voices.wav"
audio_path = "recordings/test_audio_20250411_130911.wav"


# Transcribe
result = model.transcribe(audio_path)

# Print and save the transcript
print("\n--- TRANSCRIPTION ---\n")
print(result["text"])

with open("meeting_transcript.txt", "w") as f:
    f.write(result["text"])

