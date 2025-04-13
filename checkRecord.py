# checkRecord.py
import sounddevice as sd
import soundfile as sf
import os
import datetime
import threading

# Configuration
OUTPUT_DIR = "recordings"
os.makedirs(OUTPUT_DIR, exist_ok=True)
DEVICE_INDEX = 2
SAMPLE_RATE = 44100
CHANNELS = 2
RECORD_SECONDS = 10

# Globals
recording = True
filename = os.path.join(
    OUTPUT_DIR, f"test_audio_{datetime.datetime.now().strftime('%Y%m%d_%H%M%S')}.wav"
)

def callback(indata, frames, time, status):
    if status:
        print(status)
    if recording:
        file.write(indata)

def record_audio():
    global file
    with sf.SoundFile(filename, mode='x', samplerate=SAMPLE_RATE,
                      channels=CHANNELS, subtype='PCM_16') as file:
        with sd.InputStream(samplerate=SAMPLE_RATE, channels=CHANNELS,
                            callback=callback, device=DEVICE_INDEX):
            print(f"🎤 Recording system audio from device {DEVICE_INDEX} for {RECORD_SECONDS} seconds...")
            sd.sleep(RECORD_SECONDS * 1000)

    print(f"✅ Audio saved to: {filename}")

if __name__ == "__main__":
    record_audio()
