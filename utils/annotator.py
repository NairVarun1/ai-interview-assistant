import whisper
from pyannote.audio import Pipeline
import os
import torch

def diarize_and_transcribe(audio_path):
    """
    Transcribes and diarizes audio, then saves the annotated transcript.
    :param audio_path: Path to the recorded audio file.
    :return: None
    """

    # Step 1: Transcribe with Whisper
    print("Loading Whisper model...")
    whisper_model = whisper.load_model("base")  # You can use "tiny", "base", "small", etc.
    
    print("Transcribing with Whisper...")
    whisper_result = whisper_model.transcribe(audio_path)

    # Print and save the full transcript
    print("\n--- FULL TRANSCRIPTION ---\n")
    print(whisper_result["text"])

    # Save the full transcript
    full_transcript_path = f"{os.path.splitext(audio_path)[0]}_transcript.txt"
    with open(full_transcript_path, "w") as f:
        f.write(whisper_result["text"])

    # Step 2: Set up Pyannote for speaker diarization
    print("\nSetting up Pyannote for speaker diarization...")
    diarization_pipeline = Pipeline.from_pretrained(
        "pyannote/speaker-diarization@2.1",
        use_auth_token=os.environ.get("#")  # Make sure your Hugging Face token is set up correctly
    )

    # Run the diarization on your audio file
    print("Running diarization...")
    diarization_result = diarization_pipeline(audio_path)

    # Step 3: Combine Whisper transcription with Pyannote diarization
    print("\nCombining transcription with speaker diarization...")

    # Process the Whisper segments
    whisper_segments = [{"start": seg["start"], "end": seg["end"], "text": seg["text"]} for seg in whisper_result["segments"]]

    # Create a list to store the diarized segments
    diarized_segments = []

    # Process the diarization results
    for turn, _, speaker in diarization_result.itertracks(yield_label=True):
        speaker_text = ""
        for whisper_segment in whisper_segments:
            if turn.start <= whisper_segment["end"] and turn.end >= whisper_segment["start"]:
                overlap_start = max(turn.start, whisper_segment["start"])
                overlap_end = min(turn.end, whisper_segment["end"])
                if (overlap_end - overlap_start) > 0.5:  # At least 0.5 seconds overlap
                    speaker_text += whisper_segment["text"] + " "
        if speaker_text.strip():
            diarized_segments.append({"speaker": speaker, "start": turn.start, "end": turn.end, "text": speaker_text.strip()})

    # Merge consecutive segments from the same speaker
    merged_segments = []
    current_speaker = None
    current_text = ""
    current_start = 0
    current_end = 0

    for segment in diarized_segments:
        if current_speaker != segment["speaker"]:
            if current_speaker:
                merged_segments.append({"speaker": current_speaker, "start": current_start, "end": current_end, "text": current_text.strip()})
            current_speaker = segment["speaker"]
            current_text = segment["text"]
            current_start = segment["start"]
            current_end = segment["end"]
        else:
            current_text += " " + segment["text"]
            current_end = segment["end"]

    # Add the last segment
    if current_speaker:
        merged_segments.append({"speaker": current_speaker, "start": current_start, "end": current_end, "text": current_text.strip()})

    # Create and save the diarized transcript without timestamps
    print("\n--- DIARIZED TRANSCRIPTION ---\n")
    diarized_transcript = ""
    speaker_map = {0: "Interviewer", 1: "Candidate"}  # Mapping speaker IDs to Interviewer and Candidate

    for segment in merged_segments:
        speaker_label = speaker_map.get(segment['speaker'], f"Speaker {segment['speaker']}")  # Default label for unknown speakers
        line = f"{speaker_label}: {segment['text']}"
        print(line)
        diarized_transcript += f"{line}\n"

    # Save diarized transcript
    diarized_transcript_path = f"{os.path.splitext(audio_path)[0]}_diarized.txt"
    with open(diarized_transcript_path, "w") as f:
        f.write(diarized_transcript)

    print(f"Diarized transcript saved to {diarized_transcript_path}")

