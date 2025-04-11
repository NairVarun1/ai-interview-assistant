#TO check if Blackhole as been setup as an audio device and its port.
import sounddevice as sd

print(sd.query_devices())
