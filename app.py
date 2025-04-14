# app.py

import os
import re
import time
import imaplib
import email
from icalendar import Calendar
from datetime import datetime
from apscheduler.schedulers.background import BackgroundScheduler
from selenium import webdriver
from selenium.webdriver.chrome.options import Options
from selenium.webdriver.common.by import By
from selenium.webdriver.chrome.service import Service
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from webdriver_manager.chrome import ChromeDriverManager
from audio.recorder import record_meeting_audio
from utils.annotator import diarize_and_transcribe
from utils.reportGenerator import analyse_annotated_transcript, generate_report
from utils.transcriber import transcribe_audio
from utils.annotator import diarize_and_transcribe
from utils.analyseTranscript import analyse_transcript
import threading
from dotenv import load_dotenv
load_dotenv()
EMAIL_ACCOUNT = os.getenv("EMAIL_ACCOUNT")
PASSWORD = os.getenv("EMAIL_PASSWORD")

scheduler = BackgroundScheduler()
scheduler.start()


def manual_google_login():
    print("🔐 Launching browser for manual Google login...")

    options = Options()
    options.add_argument(f"--user-data-dir=/tmp/selenium")
    options.add_argument(f"--profile-directory=Default")

    service = Service(ChromeDriverManager().install())
    driver = webdriver.Chrome(service=service, options=options)
    driver.get("https://accounts.google.com")

    input("✅ After logging in manually, press Enter to continue...")
    driver.quit()


# 4️⃣ Extract Meeting Info from .ics
def extract_meeting_details(msg):
    for part in msg.walk():
        content_type = part.get_content_type()

        if content_type == "text/calendar":
            calendar_data = part.get_payload(decode=True)
            cal = Calendar.from_ical(calendar_data)

            for component in cal.walk():
                if component.name == "VEVENT":
                    start = component.get('dtstart').dt
                    description = str(component.get('description'))
                    match = re.search(r'https://meet\.google\.com/[a-zA-Z0-9\-]+', description)
                    link = match.group() if match else None
                    return start, link

    for part in msg.walk():
        if part.get_content_type() == "text/plain":
            body = part.get_payload(decode=True).decode()
            match = re.search(r'https://meet\.google\.com/[a-zA-Z0-9\-]+', body)
            if match:
                return datetime.now(), match.group()

    return None, None


def disable_camera(driver, wait):
    print("📷 Trying to disable camera...")
    try:
        cam_xpath = '//div[@role="button" and contains(@aria-label, "camera")]'
        cam_button = wait.until(EC.presence_of_element_located((By.XPATH, cam_xpath)))
        aria_label = cam_button.get_attribute("aria-label")

        if "Turn off camera" in aria_label:
            driver.execute_script("arguments[0].click();", cam_button)
            time.sleep(1)
            print("✅ Camera disabled.")
        else:
            print("📷 Camera already off or can't detect state.")
    except Exception as e:
        print("❌ Failed to disable camera:", e)


# 5️⃣ Fetch New Meeting Emails
def check_for_meeting_invites():
    print("📧 Logging into Gmail...")
    mail = imaplib.IMAP4_SSL("imap.gmail.com")
    mail.login(EMAIL_ACCOUNT, PASSWORD)
    print("📥 Fetching unread emails...")
    mail.select("inbox")

    status, data = mail.search(None, 'UNSEEN')
    email_ids = data[0].split()
    scheduled_links = set()

    for e_id in email_ids:
        _, msg_data = mail.fetch(e_id, '(RFC822)')
        msg = email.message_from_bytes(msg_data[0][1])
        subject = msg["subject"]

        if subject and ("interview" in subject.lower() or "meeting" in subject.lower()):
            start, link = extract_meeting_details(msg)
            if start and link and link not in scheduled_links:
                print(f"📅 Scheduled: {subject} at {start} | Link: {link}")
                scheduler.add_job(join_meeting, trigger='date', run_date=start, args=[link])
                scheduled_links.add(link)

    mail.logout()


def join_meeting(link):
    print("🚀 Opening browser to join meeting:", link)

    options = Options()
    options.add_argument("--use-fake-ui-for-media-stream")
    options.add_argument("--disable-infobars")
    options.add_argument("--start-maximized")
    options.add_argument("--disable-dev-shm-usage")
    options.add_argument("--no-sandbox")
    options.add_argument("--disable-blink-features=AutomationControlled")
    options.add_argument(f"--user-data-dir=/tmp/selenium")
    options.add_argument(f"--profile-directory=Default")

    options.add_experimental_option("prefs", {
        "profile.default_content_setting_values.media_stream_camera": 2,
        "profile.default_content_setting_values.media_stream_mic": 1
    })

    service = Service(ChromeDriverManager().install())
    driver = webdriver.Chrome(service=service, options=options)
    driver.get(link)

    try:
        wait = WebDriverWait(driver, 40)

        print("🔇 Trying to disable mic...")
        mic_xpath = '//div[@aria-label="Turn off microphone"]'
        mic = wait.until(EC.element_to_be_clickable((By.XPATH, mic_xpath)))
        mic.click()

        disable_camera(driver, wait)
        time.sleep(2)

        print("🟢 Looking for Join button...")
        join_now_xpath = '//span[text()="Ask to join"]'
        join_btn = wait.until(EC.element_to_be_clickable((By.XPATH, join_now_xpath)))
        join_btn.click()
        print("✅ Clicked Join.")
        print("⏳ Waiting to confirm entry into the call...")
        
        meeting_ready_xpath = '//button[@aria-label="Meeting details"]'
        wait.until(EC.presence_of_element_located((By.XPATH, meeting_ready_xpath)))
        print("🎥 Successfully joined the call.")

        # ✅ Start recording AFTER joining
        stop_flag = {"stop": False}
        audio_file_path = None

        def stop_check():
            return stop_flag["stop"]

        def record_audio():
            nonlocal audio_file_path
            audio_file_path = record_meeting_audio(device_index=2, stop_flag=stop_check)

        audio_thread = threading.Thread(target=record_audio)
        audio_thread.start()
        print("🎙️ Recording started. Monitoring meeting...")

        print("🕵️ Monitoring meeting status...")
        meeting_ended = False
        while not meeting_ended:
            try:
                end_xpath = '//span[contains(text(), "Return to home screen") or contains(text(), "You’ve left the meeting")]'
                driver.find_element(By.XPATH, end_xpath)
                meeting_ended = True
                print("📴 Meeting has ended!")
            except:
                time.sleep(5)
        # ✅ Set stop_flag and wait for recording thread to finish
        stop_flag["stop"] = True
        audio_thread.join()
        print("🛑 Meeting ended, audio thread stopped.")

        if audio_file_path:
            diarize_and_transcribe(audio_file_path)
            print("📄 Annotated transcript saved.")

            # Path to the annotated transcript
            transcript_path = os.path.splitext(audio_file_path)[0] + "_annotated.txt"
            print(f"📄 Transcription completed, file saved at: {transcript_path}")

            # Perform sentiment analysis and relevance scoring on the annotated transcript
            results, sentiment_summary, relevance_scores, sentiment_scores = analyse_annotated_transcript(transcript_path)

            # Generate the report
            timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
            report_filename = f"report_{timestamp}.txt"
            output_path = os.path.join("test_reports", report_filename)
            os.makedirs("test_reports", exist_ok=True)
            generate_report(results, sentiment_summary, relevance_scores, sentiment_scores, output_path)

            print(f"✅ Report saved to: {output_path}")
            transcript_path = os.path.splitext(audio_file_path)[0] + "_annotated.txt"
            analyse_transcript(transcript_path)
    
            print("📊 Sentiment and Relevance analysis complete. Exiting script now.")
            exit(0)


    except Exception as e:
        print("❌ Error during meeting:", e)
    finally:
        driver.quit()

if __name__ == "__main__":
    #manual_google_login()  # Run once for session
    check_for_meeting_invites()

    while True:
        # Or manually trigger one for testing:
        # join_meeting("https://meet.google.com/xxx-xxxx-xxx")
        time.sleep(60)
