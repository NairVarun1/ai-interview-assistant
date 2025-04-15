import os
import whisper
import soundfile as sf
import librosa
import numpy as np
import re
from dotenv import load_dotenv
from pyannote.audio import Pipeline
from datetime import timedelta

load_dotenv()
HUGGINGFACE_TOKEN = os.getenv("HUGGINGFACE_TOKEN")

# Silence removal
def remove_silence(audio_path, output_path, threshold_db=-60, frame_length=2048, hop_length=512):
    try:
        y, sr = librosa.load(audio_path, sr=16000)
        intervals = librosa.effects.split(y, top_db=threshold_db, frame_length=frame_length, hop_length=hop_length)
        if len(intervals) > 0:
            trimmed_audio = np.concatenate([y[i[0]:i[1]] for i in intervals])
            sf.write(output_path, trimmed_audio, sr)
        else:
            sf.write(output_path, y, sr)
    except Exception as e:
        print(f"Error removing silence: {e}")
        return False
    return True

# Transcription
def transcribe_with_whisper(audio_path):
    print("📝 Transcribing with Whisper...")
    try:
        model = whisper.load_model("tiny")
        result = model.transcribe(audio_path, word_timestamps=False)
        return result["segments"]
    except Exception as e:
        print(f"Error during transcription: {e}")
        return None

# Diarization with pyannote
def diarize_speakers(audio_path):
    print("🔍 Performing speaker diarization...")
    try:
        pipeline = Pipeline.from_pretrained("pyannote/speaker-diarization", use_auth_token=HUGGINGFACE_TOKEN)
        diarization = pipeline(audio_path)
        return diarization
    except Exception as e:
        print(f"Error during diarization: {e}")
        return None

# Align speaker labels with transcription
def annotate_transcript(segments, diarization):
    label_map = {
        "SPEAKER_00": "Interviewer",
        "SPEAKER_01": "Candidate"
    }

    annotated_text = ""

    for segment in segments:
        seg_start = segment["start"]
        seg_end = segment["end"]
        seg_text = segment["text"].strip()

        speaker_label = "Unknown"
        max_overlap = 0

        for turn, _, label in diarization.itertracks(yield_label=True):
            turn_start = turn.start
            turn_end = turn.end

            # Calculate overlap duration
            overlap_start = max(seg_start, turn_start)
            overlap_end = min(seg_end, turn_end)
            overlap = max(0, overlap_end - overlap_start)

            if overlap > max_overlap:
                max_overlap = overlap
                speaker_label = label_map.get(label, "Unknown")

        annotated_text += f"{speaker_label}: {seg_text}\n"

    return annotated_text


# Main flow
def transcribe_audio(audio_path):
    print("✂️ Removing silence...")
    temp_silent_removed = "silent_removed.wav"
    if not remove_silence(audio_path, temp_silent_removed):
        print("Silence removal failed. Continuing with original audio.")
        temp_silent_removed = audio_path

    segments = transcribe_with_whisper(temp_silent_removed)
    diarization = diarize_speakers(temp_silent_removed)

    if temp_silent_removed != audio_path:
        os.remove(temp_silent_removed)

    if segments and diarization:
        annotated_text = annotate_transcript(segments, diarization)

        os.makedirs("recordings", exist_ok=True)
        base_name = os.path.splitext(os.path.basename(audio_path))[0]
        transcript_path = os.path.join("recordings", f"{base_name}_annotated.txt")

        with open(transcript_path, "w") as f:
            f.write(annotated_text)

        print(f"\n✅ Annotated transcript saved to: {transcript_path}\n")
        print(annotated_text)
        return transcript_path

if __name__=="__main__":
    transcribe_audio("recordings/meeting_audio_20250415_223508.wav")