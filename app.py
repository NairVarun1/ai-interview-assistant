# 1️⃣ Imports
import imaplib, email, re
from icalendar import Calendar
from apscheduler.schedulers.background import BackgroundScheduler
from datetime import datetime
import time
from selenium import webdriver
from selenium.webdriver.chrome.options import Options
from selenium.webdriver.common.by import By
from webdriver_manager.chrome import ChromeDriverManager
from selenium.webdriver.chrome.service import Service
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from selenium.webdriver.common.action_chains import ActionChains
import time

EMAIL_ACCOUNT = "vroon0048@gmail.com"
PASSWORD = "uiht updu xrfq uqta"

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
    # First, try .ics calendar attachments
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

    # If no .ics data, fall back to parsing email body
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
        # Wait until the button is present in DOM
        cam_xpath = '//div[@role="button" and contains(@aria-label, "camera")]'
        cam_button = wait.until(EC.presence_of_element_located((By.XPATH, cam_xpath)))

        # Extra debug
        print("🎯 camera button HTML:", cam_button.get_attribute("outerHTML"))

        aria_label = cam_button.get_attribute("aria-label")
        aria_pressed = cam_button.get_attribute("aria-pressed")
        print(f"🎯 aria-label: {aria_label}")
        print(f"🎯 aria-pressed: {aria_pressed}")

        if "Turn off camera" in aria_label:
            # Try JS click
            driver.execute_script("arguments[0].click();", cam_button)
            time.sleep(1)
            print("✅ Camera disabled.")
        else:
            print("📷 Camera already off or can't detect state.")

    except Exception as e:
        print("❌ Failed to disable camera:", e)

# 5️⃣ Fetch New Meeting Emails
def check_for_meeting_invites():
    mail = imaplib.IMAP4_SSL("imap.gmail.com")
    mail.login(EMAIL_ACCOUNT, PASSWORD)
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

    print("⚠️ No meeting link found in this email.")
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
        print("✅ Mic disabled.")

        print("📷 Trying to disable camera...")

        # Try to find the camera button (regardless of current state)
        disable_camera(driver, wait)

        time.sleep(2)

        print("🟢 Looking for Join button...")
        try:
            join_now_xpath = '//span[text()="Ask to join"]'
            join_btn = wait.until(EC.element_to_be_clickable((By.XPATH, join_now_xpath)))
            join_btn.click()
            print("✅ Clicked Join.")
        except Exception as e:
            print("❌ Couldn't find join button:", e)

    except Exception as e:
        print("❌ Failed to join:", e)


if __name__ == "__main__":
        check_for_meeting_invites()

    #manual_google_login()  # <- run once to login to account then the creds are stored in selenium cookie, then comment this out
        while True:
        #join_meeting("https://meet.google.com/rzj-ccsg-bpx?pli=1")
        #join_meeting("https://meet.google.com/xxz-vucp-qps")
            time.sleep(60)
