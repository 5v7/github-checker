from selenium import webdriver
from selenium.webdriver.chrome.options import Options
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from selenium.webdriver.common.action_chains import ActionChains
import time
import requests
import random
import string
import json
import os

WEBHOOK_URL = "https://discord.com/api/webhooks/1351605146873761885/WinjaddLxcbnKYMby7jc-VEhz5LwYUoPSPhVNBTx2A5nWkLvGVijpxnoAVTlYXVUphbr"
CHECKED_FILE = "checked_usernames-2-3c.json"

def load_checked_usernames():
    if os.path.exists(CHECKED_FILE):
        with open(CHECKED_FILE, 'r') as f:
            return json.load(f)
    return {}

def save_checked_usernames(checked_dict):
    with open(CHECKED_FILE, 'w') as f:
        json.dump(checked_dict, f, indent=4)

def send_to_discord(username):
    payload = {"content": f"Available GitHub username found: {username}"}
    requests.post(WEBHOOK_URL, json=payload)

def generate_random_username(checked_dict):
    letters = string.ascii_letters
    digits = string.digits
    
    two_char_patterns = [
        lambda: random.choice(letters) + random.choice(letters),
        lambda: random.choice(letters) + random.choice(digits),
        lambda: random.choice(digits) + random.choice(letters),
        lambda: random.choice(digits) + random.choice(digits)
    ]
    
    three_char_patterns = [
        lambda: random.choice(letters) + random.choice(letters) + random.choice(letters),
        lambda: random.choice(letters) + random.choice(letters) + random.choice(digits),
        lambda: random.choice(letters) + random.choice(digits) + random.choice(letters),
        lambda: random.choice(digits) + random.choice(letters) + random.choice(letters),
        lambda: random.choice(letters) + random.choice(digits) + random.choice(digits),
        lambda: random.choice(digits) + random.choice(letters) + random.choice(digits),
        lambda: random.choice(digits) + random.choice(digits) + random.choice(letters),
        lambda: random.choice(digits) + random.choice(digits) + random.choice(digits)
    ]
    
    pattern_choice = random.choices(
        [two_char_patterns, three_char_patterns],
        weights=[0.5, 0.5],
        k=1
    )[0]
    
    while True:
        username = random.choice(pattern_choice)()
        if username not in checked_dict:
            return username

chrome_options = Options()
chrome_options.add_argument("--log-level=3")

try:
    checked_usernames = load_checked_usernames()
    driver = webdriver.Chrome(options=chrome_options)
    driver.get("https://github.com/login")
    
    while True:
        user_input = input("Type 'ok' when ready: ").strip().lower()
        if user_input == "ok":
            break
        print("Please type 'ok' when you're on the admin settings page")
    
    print("Starting username checking process...")
    
    change_username_button = WebDriverWait(driver, 10).until(
        EC.element_to_be_clickable((By.XPATH, "//span[contains(text(), 'Change username')]"))
    )
    change_username_button.click()
    
    understand_button = WebDriverWait(driver, 10).until(
        EC.element_to_be_clickable((By.XPATH, "//span[contains(text(), 'I understand, let’s change my username')]"))
    )
    understand_button.click()
    
    time.sleep(3)
    
    enter_username_header = WebDriverWait(driver, 10).until(
        EC.element_to_be_clickable((By.XPATH, '//h3[@class="Box-title" and contains(text(), "Enter a new username")]'))
    )
    enter_username_header.click()
    
    username_input = WebDriverWait(driver, 15).until(
        EC.presence_of_element_located((By.XPATH, "//input[@name='login' and @class='form-control']"))
    )
    
    attempts = 0
    while True:
        username = generate_random_username(checked_usernames)
        attempts += 1
        
        username_input.clear()
        username_input.send_keys(username)
        
        actions = ActionChains(driver)
        actions.move_to_element_with_offset(username_input, 0, -20).click().perform()
        
        time.sleep(2)
        
        try:
            availability_message = WebDriverWait(driver, 10).until(
                EC.presence_of_element_located((By.CLASS_NAME, "note"))
            )
            message_text = availability_message.text.lower()
            
            if "is not available" in message_text:
                print(f"[{attempts}] Username {username} is not available")
                checked_usernames[username] = "unavailable"
            else:
                print(f"[{attempts}] Username {username} is available!")
                checked_usernames[username] = "available"
                send_to_discord(username)
                
        except:
            print(f"[{attempts}] Username {username} is available!")
            checked_usernames[username] = "available"
            send_to_discord(username)
        
        save_checked_usernames(checked_usernames)
        time.sleep(2)

except Exception as e:
    print(f"An error occurred: {str(e)}")
    print(f"Current URL at error: {driver.current_url if 'driver' in locals() else 'Not available'}")
    if 'driver' in locals():
        print(f"Page source snippet: {driver.page_source[:500]}...")

finally:
    try:
        if 'checked_usernames' in locals():
            save_checked_usernames(checked_usernames)
            print(f"Saved {len(checked_usernames)} checked usernames to {CHECKED_FILE}")
        time.sleep(2)
        driver.quit()
        print("Browser closed")
    except:
        pass