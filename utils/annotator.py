import os
import whisper
import soundfile as sf
import librosa
import re
import numpy as np
from dotenv import load_dotenv

load_dotenv()

def remove_silence(audio_path, output_path, threshold_db=-60, frame_length=2048, hop_length=512):
    """Removes silence from an audio file."""
    try:
        y, sr = librosa.load(audio_path, sr=16000)
        intervals = librosa.effects.split(y, top_db=threshold_db, frame_length=frame_length, hop_length=hop_length)

        if len(intervals) > 0:
            trimmed_audio = np.concatenate([y[i[0]:i[1]] for i in intervals])
            sf.write(output_path, trimmed_audio, sr)
        else:
            print("Warning: No non-silent intervals found. Writing original audio.")
            sf.write(output_path, y, sr)

    except Exception as e:
        print(f"Error removing silence: {e}")
        return False
    return True

def transcribe_with_whisper(audio_path):
    """Transcribes an audio file using plain Whisper with timestamps."""
    print("📝 Transcribing with Whisper...")
    try:
        model = whisper.load_model("tiny")  # Use "tiny" for CPU
        result = model.transcribe(audio_path, word_timestamps=False)
        return result["segments"]
    except Exception as e:
        print(f"Error during transcription: {e}")
        return None

def annotate_speakers_interview(segments): #function name corrected
    speaker = "Interviewer"  # Initial speaker
    previous_speaker = None
    annotated_text = ""
    current_turn = ""

    interviewer_keywords = re.compile(r"\b(question|tell me|explain|discuss)\b", re.IGNORECASE)
    candidate_keywords = re.compile(r"\b(i|my|me)\b", re.IGNORECASE)

    duration_threshold = 2.0  # Initial threshold, will be adjusted.
    word_count_threshold = 5  # Initial threshold, will be adjusted.

    for segment in segments:
        start = segment["start"]
        end = segment["end"]
        text = segment["text"].strip()
        duration = end - start
        word_count = len(text.split())

        if interviewer_keywords.search(text):
            speaker = "Interviewer"
        elif candidate_keywords.search(text):
            speaker = "Candidate"

        if speaker == previous_speaker:
            current_turn += " " + text
        else:
            if current_turn:
                annotated_text += f"{previous_speaker}: {current_turn}\n"
            current_turn = text

        previous_speaker = speaker

        # Dynamic Threshold Adjustment
        duration_threshold = np.clip(duration * 0.8, 1.5, 5.0)  # Adjust based on current turn
        word_count_threshold = np.clip(word_count * 0.6, 3, 10) # Adjust based on current turn.

        if duration > duration_threshold and word_count > word_count_threshold:
            speaker = "Candidate" if speaker == "Interviewer" else "Interviewer"

    if current_turn:
        annotated_text += f"{speaker}: {current_turn}\n"

    return annotated_text

def transcribe_audio(audio_path):
    """Transcribes and annotates audio."""
    print("✂️ Removing silence...")
    temp_silent_removed = "silent_removed.wav"
    if not remove_silence(audio_path, temp_silent_removed):
        print("Silence removal failed. Continuing with original audio.")
        temp_silent_removed = audio_path

    segments = transcribe_with_whisper(temp_silent_removed)
    if temp_silent_removed != audio_path:
        os.remove(temp_silent_removed)

    if segments:
        annotated_text = annotate_speakers_interview(segments)

        # Ensure 'annotated/' directory exists
        os.makedirs("recordings", exist_ok=True)

        # Create annotated file path in annotated/ directory
        base_name = os.path.splitext(os.path.basename(audio_path))[0]
        transcript_path = os.path.join("recordings", f"{base_name}_annotated.txt")

        with open(transcript_path, "w") as f:
            f.write(annotated_text)

        print(f"\n✅ Annotated transcript saved to: {transcript_path}\n")
        print(annotated_text)
        return transcript_path