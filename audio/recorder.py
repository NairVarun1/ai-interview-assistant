# recorder.py
import sounddevice as sd
import soundfile as sf
import queue
import threading

q = queue.Queue()
recording = False

def audio_callback(indata, frames, time, status):
    if recording:
        q.put(indata.copy())

def record_meeting_audio(output_file="meeting_audio.wav", device_index=2):
    global recording
    recording = True
    samplerate = 44100

    with sf.SoundFile(output_file, mode='w', samplerate=samplerate, channels=2) as file:
        with sd.InputStream(samplerate=samplerate, device=device_index, channels=2, callback=audio_callback):
            print("🎙️ Recording started...")
            while recording:
                file.write(q.get())
    print("🛑 Recording stopped and saved:", output_file)

def stop_recording():
    global recording
    recording = False
