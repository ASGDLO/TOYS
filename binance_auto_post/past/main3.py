import json
import time
import os
import platform
import pyperclip  # New import for clipboard operations
from selenium import webdriver
from selenium.webdriver.chrome.service import Service as ChromeService
from selenium.webdriver.chrome.options import Options
from selenium.webdriver.common.by import By
from selenium.webdriver.common.keys import Keys  # Make sure to import Keys if you're using it
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC

# Import necessary exceptions
from selenium.common.exceptions import (
    TimeoutException,
    NoSuchElementException,
    ElementClickInterceptedException
)

# ----------------------------
# Configuration Parameters
# ----------------------------

# Path to your ChromeDriver
CHROME_DRIVER_PATH = '/usr/local/bin/chromedriver'  # Update as needed

# Paths to save cookies and local storage
COOKIES_PATH = 'cookies.json'
LOCAL_STORAGE_PATH = 'local_storage.json'

# Binance URLs
LOGIN_URL = 'https://www.binance.com/en/login'
PROFILE_URL = 'https://www.binance.com/en/square'

# Time to wait for manual login (in seconds)
MANUAL_LOGIN_WAIT_TIME = 10  

# Time to wait after saving cookies and storage before posting
WAIT_AFTER_EXTRACTION = 10  # 10 seconds

# ----------------------------
# Helper Functions
# ----------------------------

def save_cookies(driver, path):
    """Save cookies to a JSON file."""
    cookies = driver.get_cookies()
    with open(path, 'w') as file:
        json.dump(cookies, file)
    print(f"Cookies have been saved to '{path}'.")

def save_local_storage(driver, path):
    """Save local storage to a JSON file."""
    local_storage = driver.execute_script("return window.localStorage;")
    with open(path, 'w') as file:
        json.dump(local_storage, file)
    print(f"Local storage has been saved to '{path}'.")

def load_cookies(driver, path):
    """Load cookies from a JSON file into the browser."""
    if not os.path.exists(path):
        print(f"No cookies file found at '{path}'. Skipping cookie loading.")
        return
    with open(path, 'r') as file:
        cookies = json.load(file)
    for cookie in cookies:
        # Selenium expects expiry to be int
        if 'expiry' in cookie:
            cookie['expiry'] = int(cookie['expiry'])
        try:
            driver.add_cookie(cookie)
        except Exception as e:
            print(f"Error adding cookie {cookie}: {e}")
    print("Cookies loaded successfully.")

def load_local_storage(driver, path):
    """Load local storage from a JSON file into the browser."""
    if not os.path.exists(path):
        print(f"No local storage file found at '{path}'. Skipping local storage loading.")
        return
    with open(path, 'r') as file:
        local_storage = json.load(file)
    for key, value in local_storage.items():
        # Sanitize the value to prevent JavaScript injection
        sanitized_value = value.replace("'", "\\'").replace('"', '\\"')
        script = f"window.localStorage.setItem('{key}', '{sanitized_value}');"
        driver.execute_script(script)
    print("Local storage loaded successfully.")

def load_post_text(file_path):
    """Load post text from a specified file."""
    if not os.path.exists(file_path):
        print(f"Post text file not found at '{file_path}'. Using default text.")
        return "Default post text."
    
    with open(file_path, 'r') as file:
        content = file.read().strip()
    
    print(f"Post text loaded from '{file_path}'.")
    return content

def paste_text(driver, element, text):
    """Paste text into the specified element using clipboard for faster insertion."""
    pyperclip.copy(text)
    element.click()
    if platform.system() == 'Darwin':
        element.send_keys(Keys.COMMAND, 'v')  # For macOS
    else:
        element.send_keys(Keys.CONTROL, 'v')  # For Windows/Linux
    print(f"Pasted text into post editor: {text}")

def perform_posting(driver, post_text):
    """Automate the blog posting process."""
    wait = WebDriverWait(driver, 10)  # Increased timeout to 10 seconds

    try:
        # Navigate to the Profile Page
        driver.get(PROFILE_URL)
        print(f"Navigated to profile page: {PROFILE_URL}")

        # Updated locator for the new <p> element
        post_editor = wait.until(EC.element_to_be_clickable(
            (By.XPATH, "//p[contains(@class, 'selected') and @data-placeholder='Share your thoughts']")
        ))
        print("Post editor is visible.")

        # Click on the editor to focus
        post_editor.click()

        # Clear existing text using JavaScript
        driver.execute_script("arguments[0].innerHTML = '';", post_editor)
        print("Cleared existing text in the post editor.")

        # Insert the desired text using paste_text
        paste_text(driver, post_editor, post_text)

        # Click the 'Post' button
        post_button = wait.until(EC.element_to_be_clickable(
            (By.XPATH, "//button[@data-bn-type='button' and .//span[text()='Post']]")
        ))
        post_button.click()
        print("Clicked the 'Post' button.")

    except Exception as e:
        print(f"An error occurred during posting: {e}")

# ----------------------------
# Main Execution Flow
# ----------------------------

def main():
    # Path to the post text file
    POST_TEXT_FILE = '/home/ethan/Documents/GitHub/TOY/binance_auto_post/chatgpt_response.txt'
    
    # Configure ChromeOptions
    chrome_options = Options()
    # Use a temporary profile to avoid conflicts
    chrome_options.add_argument('--user-data-dir=/tmp/temp_profile')
    # Optional: Run Chrome in headless mode
    # chrome_options.add_argument('--headless')
    # Optional: Disable GPU (useful for headless mode)
    # chrome_options.add_argument('--disable-gpu')
    # Optional: Ignore certificate errors
    chrome_options.add_argument('--ignore-certificate-errors')
    # Optional: Start maximized
    chrome_options.add_argument('--start-maximized')

    # Initialize the Chrome WebDriver
    service = ChromeService(executable_path=CHROME_DRIVER_PATH)
    driver = webdriver.Chrome(service=service, options=chrome_options)

    try:
        # Phase 1: Manual Login and Extraction
        print("=== Phase 1: Manual Login and Extraction ===")
        driver.get(LOGIN_URL)
        print(f"Navigated to {LOGIN_URL}")
        print(f"Please log in manually within the next {MANUAL_LOGIN_WAIT_TIME} seconds.")
        time.sleep(MANUAL_LOGIN_WAIT_TIME)  # Wait for manual login

        # After login, save cookies and local storage
        save_cookies(driver, COOKIES_PATH)
        save_local_storage(driver, LOCAL_STORAGE_PATH)

        # Phase 2: Automated Blog Posting
        print("\n=== Phase 2: Automated Blog Posting ===")
        print(f"Waiting for {WAIT_AFTER_EXTRACTION} seconds before proceeding to post.")
        time.sleep(WAIT_AFTER_EXTRACTION)

        # Reload the page to ensure cookies and local storage are applied
        driver.refresh()
        print("Page refreshed to apply authentication.")

        # Load the post text from the file
        post_text = load_post_text(POST_TEXT_FILE)

        # Perform the blog posting
        perform_posting(driver, post_text)

    except Exception as e:
        print(f"An unexpected error occurred: {e}")

    finally:
        # Close the browser after a short delay to observe the result
        time.sleep(5)
        driver.quit()
        print("Browser closed.")

if __name__ == "__main__":
    main()