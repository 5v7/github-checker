from selenium import webdriver
from selenium.webdriver.chrome.options import Options
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from selenium.webdriver.common.action_chains import ActionChains
from selenium.common.exceptions import InvalidSessionIdException, WebDriverException, TimeoutException
import time
import requests
import random
import string
import json
import os
import re

WEBHOOK_URL = ""  # Replace with your Discord webhook URL
CHECKED_FILE = "checked_usernames-3-4c.json"

def load_checked_usernames():
    if os.path.exists(CHECKED_FILE):
        with open(CHECKED_FILE, 'r') as f:
            return json.load(f)
    return {}

def save_checked_usernames(checked_dict):
    with open(CHECKED_FILE, 'w') as f:
        json.dump(checked_dict, f, indent=4)

def send_to_discord(username, length):
    if not WEBHOOK_URL:
        print(f"Webhook URL not set. Skipping Discord notification for {username}")
        return
    
    color = 0xFF0000 if length == 3 else 0x0000FF  
    embed = {
        "title": f"Available GitHub Username ({length} chars)",
        "description": f"Username: **{username}**",
        "color": color,
        "timestamp": time.strftime("%Y-%m-%dT%H:%M:%SZ", time.gmtime())
    }
    payload = {"embeds": [embed]}
    try:
        requests.post(WEBHOOK_URL, json=payload)
        print(f"Sent {username} to Discord")
    except requests.exceptions.RequestException as e:
        print(f"Failed to send to Discord: {str(e)}")

def generate_random_username(checked_dict, mode):
    letters = string.ascii_lowercase
    digits = string.digits
    
    three_char_patterns = [
        lambda: ''.join(random.choice(letters) for _ in range(3)),
        lambda: random.choice(letters) + random.choice(letters) + random.choice(digits),
        lambda: random.choice(letters) + random.choice(digits) + random.choice(letters),
        lambda: random.choice(digits) + random.choice(letters) + random.choice(letters),
        lambda: random.choice(letters) + random.choice(digits) + random.choice(digits),
        lambda: random.choice(digits) + random.choice(letters) + random.choice(digits),
        lambda: random.choice(digits) + random.choice(digits) + random.choice(letters),
        lambda: ''.join(random.choice(digits) for _ in range(3))
    ]
    
    four_char_patterns = [
        lambda: ''.join(random.choice(letters) for _ in range(4)),  
        lambda: ''.join(random.choice(digits) for _ in range(4))  
    ]
    
    pattern_choices = three_char_patterns if mode == '3c' else four_char_patterns if mode == '4c' else three_char_patterns + four_char_patterns
    while True:
        username = random.choice(pattern_choices)()
        if username not in checked_dict:
            return username

def fetch_wordlist(url):
    try:
        response = requests.get(url)
        response.raise_for_status()
        words = response.text.splitlines()
        valid_words = [w.strip() for w in words if re.match(r'^[a-zA-Z0-9](?:[a-zA-Z0-9-]{0,37}[a-zA-Z0-9])?$', w) and '--' not in w]
        print(f"Fetched {len(words)} words, {len(valid_words)} valid after filtering")
        return valid_words
    except requests.exceptions.RequestException as e:
        print(f"Failed to fetch wordlist from {url}: {str(e)}")
        return []

def setup_driver():
    chrome_options = Options()
    chrome_options.add_argument("--log-level=3")
    chrome_options.add_argument("--no-sandbox")
    chrome_options.add_argument("--disable-dev-shm-usage")
    return webdriver.Chrome(options=chrome_options)

def initialize_form(driver):
    print("Initializing username change form...")
    driver.get("https://github.com/settings/admin")
    
    change_button = WebDriverWait(driver, 10).until(
        EC.element_to_be_clickable((By.XPATH, "//span[@class='Button-label' and contains(text(), 'Change username')]"))
    )
    change_button.click()
    
    understand_button = WebDriverWait(driver, 10).until(
        EC.element_to_be_clickable((By.XPATH, "//span[@class='Button-label' and contains(text(), 'I understand, let’s change my username')]"))
    )
    understand_button.click()
    
    dialog_title = WebDriverWait(driver, 10).until(
        EC.element_to_be_clickable((By.ID, "rename-form-dialog-title"))
    )
    dialog_title.click()
    
    username_input = WebDriverWait(driver, 15).until(
        EC.element_to_be_clickable((By.ID, "login"))
    )
    print("Form initialized successfully")
    return username_input

while True:
    mode = input("Choose mode (3c for 3-char, 4c for 4-char [letters or numbers], all for both, words for wordlist): ").strip().lower()
    if mode in ['3c', '4c', 'all', 'words']:
        break
    print("Invalid choice. Please enter '3c', '4c', 'all', or 'words'.")

wordlist = None
if mode == 'words':
    url = input("Enter URL to wordlist (e.g., https://raw.githubusercontent.com/dwyl/english-words/refs/heads/master/words.txt): ").strip()
    wordlist = fetch_wordlist(url)
    if not wordlist:
        print("No valid words fetched. Exiting.")
        exit(1)

total_3c = 36**3
total_4c_current = (26**4) + (10**4)  
total_all = total_3c + total_4c_current  
check_time_per_username = 4  

print(f"Estimated time to check all possibilities for mode '{mode}':")
if mode == '3c':
    total_time = total_3c * check_time_per_username / 3600
    print(f"3C: ~{total_time:.2f} hours (~{total_time/24:.2f} days)")
elif mode == '4c':
    total_time = total_4c_current * check_time_per_username / 3600
    print(f"4C (4 letters or 4 numbers): ~{total_time:.2f} hours (~{total_time/24:.2f} days)")
elif mode == 'all':
    total_time = total_all * check_time_per_username / 3600
    print(f"All (3C + 4C): ~{total_time:.2f} hours (~{total_time/24:.2f} days)")
elif mode == 'words':
    total_time = len(wordlist) * check_time_per_username / 3600
    print(f"Words ({len(wordlist)} entries): ~{total_time:.2f} hours (~{total_time/24:.2f} days)")

checked_usernames = load_checked_usernames()
driver = None

try:
    driver = setup_driver()
    driver.get("https://github.com/login")
    
    while True:
        user_input = input("Type 'ok' when ready (after logging in and reaching settings/admin): ").strip().lower()
        if user_input == "ok":
            break
        print("Please type 'ok' when you're on the admin settings page")
    
    username_input = initialize_form(driver)
    print("Starting username checking process...")
    
    attempts = 0
    if mode == 'words':
        word_iterator = iter(wordlist)
    while True:
        try:
            if mode == 'words':
                try:
                    username = next(word_iterator)
                    if username in checked_usernames:
                        continue
                except StopIteration:
                    print("Wordlist exhausted. Stopping.")
                    break
            else:
                username = generate_random_username(checked_usernames, mode)
            
            attempts += 1
            print(f"[{attempts}] Checking username: {username}")
            username_input.clear()
            username_input.send_keys(username)
            time.sleep(1)  
            
            actions = ActionChains(driver)
            actions.move_to_element_with_offset(username_input, 0, -20).click().perform()
            
            try:
                WebDriverWait(driver, 5).until(
                    EC.presence_of_element_located((By.CLASS_NAME, "color-fg-danger"))
                )
                print(f"[{attempts}] Username {username} is not available")
                checked_usernames[username] = "unavailable"
            except TimeoutException:
                try:
                    WebDriverWait(driver, 2).until(
                        EC.presence_of_element_located((By.CLASS_NAME, "color-fg-success"))
                    )
                    print(f"[{attempts}] Username {username} is available!")
                    checked_usernames[username] = "available"
                    send_to_discord(username, len(username))
                except TimeoutException:
                    print(f"[{attempts}] Username {username} is available! (no error or success message detected)")
                    checked_usernames[username] = "available"
                    send_to_discord(username, len(username))
            
            save_checked_usernames(checked_usernames)
            time.sleep(random.uniform(2, 4))  
        
        except (InvalidSessionIdException, WebDriverException) as e:
            print(f"Session lost: {str(e)}. Restarting browser...")
            if driver:
                driver.quit()
            driver = setup_driver()
            username_input = initialize_form(driver)
            print("Browser restarted and setup complete. Resuming checks...")

except Exception as e:
    print(f"An error occurred: {str(e)}")
    print(f"Current URL at error: {driver.current_url if driver else 'Not available'}")
    if driver:
        print(f"Page source snippet: {driver.page_source[:500]}...")

finally:
    if 'checked_usernames' in locals():
        save_checked_usernames(checked_usernames)
        print(f"Saved {len(checked_usernames)} checked usernames to {CHECKED_FILE}")
    if driver:
        driver.quit()
        print("Browser closed")