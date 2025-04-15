# 🤖 AI Interview Assistant

An AI Bot that can be a part of meetings, capture real-time candidate responses, analyze them, and provide actionable insights to the recruiter.

---

## 📌 Overview

The **AI Interview Assistant** automates the interview process by:
- Reading Gmail invites
- Extracting Google Meet links
- Joining meetings via Selenium
- Recording and transcribing the conversation
- Performing sentiment and relevance analysis
- Saving detailed reports for recruiters

---

## 🛠️ Tech Stack Summary

| Layer         | Tools/Tech Used                                           |
|---------------|-----------------------------------------------------------|
| Automation    | Python, Selenium                                          |
| Audio         | macOS BlackHole, PyAudio, `ffmpeg`, OpenAI Whisper        |
| AI Features   | Transcription, Diarization, Sentiment Analysis, Relevance |
| Email Access  | Gmail IMAP                                                |
| DevOps        | Git, GitHub                                               |

---

## 🎯 Functional Flow

### 1. **Login via Google Manually**
- One-time browser login handled via Selenium
- Saves session cookies for re-use

### 2. **Read Meeting Invites**
- Connects to Gmail via IMAP

### 3. **Join Google Meet Automatically**
- Disables mic/cam
- Clicks **Ask to Join** and joins the call

### 4. **Capture Meeting Audio**
- Uses `BlackHole` (macOS virtual device)
- Captures only Google Meet audio using `ffmpeg`
- Stores audio as `.wav` in `/recordings`

### 5. **Transcribe & Annotate**
- Removes silence via `librosa`
- Transcribes using **Whisper**
- Automatically labels speaker as **Interviewer** or **Candidate**
- Saves transcript as `.txt`
- Does annotation by using pyannote

### 6. **Analyze Conversation**
- Performs:
  - Sentiment analysis on candidate responses
  - Relevance scoring for each answer
- Stores full report as `.json` and `.txt`

---

## 🔮 AI + Analysis Pipeline

### Whisper Transcription

```python
import whisper
model = whisper.load_model("base", device="cpu")
segments = model.transcribe("audio.wav")

### 🛠️ Full Setup Guide for AI Interview Assistant (macOS)

## 1️⃣ Clone the Repository

git clone https://github.com/your-username/ai-interview-assistant.git
cd ai-interview-assistant

## 2. Create a virtual environment and install dependencies

python3 -m venv .venv
source .venv/bin/activate

## 3. Install "ffmpeg" to record chrome audio

brew install ffmpeg
Verify : ffmpeg -version

## 4. Setup BlackHole

brew install "blackhole_2ch"
# Configure Audio Devices

- Open Audio MIDI Setup on macOS.

- Click ➕ in the bottom-left and choose Create Multi-Output Device.

Select:

- Your Mac's Output (e.g., MacBook Speakers)

- "BlackHole-2ch"

- Include your Mac’s built-in microphone and "BlackHole-2ch"

- Go to System Settings > Sound:

- Input: Set to "BlackHole_2ch"

- Output: Set to Multi-Output Device

## 5. Add Environment Variables

- Create a .env file in root directory

-EMAIL=your_email@gmail.com
-EMAIL_APP_PASSWORD=your_generated_app_password(Make sure 2FA is setup on the google account)
-HUGGINGFACE_TOKEN=your_huggingface_token

## 6.Run the App

python app.py

## If you add new packages:

- pip freeze > requirements.txt
