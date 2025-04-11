# 📘 AI Interview Assistant - Project Documentation

---

## 📌 Overview

The **AI Interview Assistant** automates interview attendance by reading Gmail invites, extracting Google Meet links, joining the calls via Selenium, and (in future steps) capturing and transcribing candidate audio using AI. It's designed to integrate with platforms like **PeopleHum** to support seamless virtual hiring.

---

## 🛠️ Tech Stack Summary

| Layer         | Tools/Tech Used                                           |
|---------------|-----------------------------------------------------------|
| Automation    | Python, Selenium, imaplib, icalendar                      |
| Audio         | MacOS BlackHole, PyAudio, OpenAI Whisper                  |
| AI Features   | Whisper (Transcription), Future: Sentiment, Plagiarism   |
| Scheduling    | APScheduler                                               |
| Email Access  | Gmail IMAP                                                |
| DevOps        | Git, GitHub                                               |

---

## 🎯 Functional Flow

1. **Manual Google Login**  
   - Opens browser once to login manually using Selenium  
   - Stores session cookies for automation

2. **Read Meeting Invites**  
   - Connects to Gmail using IMAP  
   - Scans unread messages for meeting invites or `.ics` attachments  
   - Extracts Meet links and schedules `join_meeting()` at proper time

3. **Join Google Meet Automatically**  
   - Opens Chrome with the correct profile  
   - Disables mic/camera  
   - Clicks **Ask to Join**

4. **Capture Audio from Meet (WIP)**  
   - Uses BlackHole virtual audio device on Mac  
   - Records system audio during Meet session  
   - Saves to `.wav` file

5. **Transcribe Audio**  
   - Loads `.wav` into OpenAI Whisper model  
   - Generates accurate transcript  
   - Saves transcript as `.txt`

---

## 🌐 Backend API (Future Integration)

To integrate with PeopleHum or similar platforms, backend APIs may include:

### POST `/api/interview/join`
- Input: Email invite details  
- Action: Schedule job + attend meet

### POST `/api/audio/save`
- Input: Audio blob or file path  
- Action: Transcribe & store result

---

## 🎤 Model Workflow (`transcriber/whisper_transcribe.py`)

### Audio Transcription Flow

- Accept `.wav` file recorded during the call  
- Process using:
```python
import whisper
model = whisper.load_model("base")
result = model.transcribe("audio.wav")
