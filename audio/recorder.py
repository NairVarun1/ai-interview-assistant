# audio/recorder.py
import sounddevice as sd
import soundfile as sf
import queue
import os
from datetime import datetime

q = queue.Queue()

def audio_callback(indata, frames, time, status):
    if status:
        print("⚠️", status)
    q.put(indata.copy())

def record_meeting_audio(output_dir="recordings", device_index=2, stop_flag=None):
    samplerate = 44100
    channels = 2
    recording = True

    os.makedirs(output_dir, exist_ok=True)
    filename = f"meeting_audio_{datetime.now().strftime('%Y%m%d_%H%M%S')}.wav"
    output_path = os.path.join(output_dir, filename)

    try:
        with sf.SoundFile(output_path, mode='w', samplerate=samplerate, channels=channels) as file:
            with sd.InputStream(samplerate=samplerate, device=device_index, channels=channels, callback=audio_callback):
                print(f"🎙️ Recording started on device {device_index}...")
                while recording and (stop_flag is None or not stop_flag()):
                    try:
                        data = q.get(timeout=1)
                        file.write(data)
                    except queue.Empty:
                        continue
        print("🛑 Recording stopped and saved:", output_path)
    except Exception as e:
        print("❌ Error while recording:", e)
        return None

    return output_path
