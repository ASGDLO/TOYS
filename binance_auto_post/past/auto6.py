import os
import time
import traceback
import logging
import sys
import platform
import pyperclip
from functools import wraps

import undetected_chromedriver as uc
from selenium.webdriver.common.by import By
from selenium.webdriver.common.keys import Keys
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from selenium.webdriver.common.action_chains import ActionChains
from selenium.common.exceptions import (
    TimeoutException,
    NoSuchElementException,
    ElementClickInterceptedException
)

# ----------------------------
# Configure Logging
# ----------------------------

logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s [%(levelname)s] %(message)s',
    handlers=[
        logging.FileHandler("automation.log"),
        logging.StreamHandler()
    ]
)
logger = logging.getLogger(__name__)

# ----------------------------
# Retry Decorator
# ----------------------------

def retry(max_attempts=3, delay=5, exceptions=(Exception,), on_failure=None):
    """
    Decorator to retry a function upon encountering specified exceptions.
    """
    def decorator(func):
        @wraps(func)
        def wrapper(*args, **kwargs):
            attempts = 0
            while attempts < max_attempts:
                try:
                    return func(*args, **kwargs)
                except exceptions as e:
                    attempts += 1
                    logger.warning(f"Attempt {attempts} for {func.__name__} failed with error: {e}")
                    if attempts < max_attempts:
                        logger.info(f"Retrying {func.__name__} in {delay} seconds...")
                        time.sleep(delay)
                    else:
                        logger.error(f"All {max_attempts} attempts for {func.__name__} failed.")
                        if on_failure:
                            on_failure()
                        raise
        return wrapper
    return decorator

# ----------------------------
# Driver Initialization
# ----------------------------

@retry(max_attempts=3, delay=5, exceptions=(Exception,))
def initialize_driver():
    """
    Initialize the Chrome driver with specified options.
    """
    chrome_user_data_dir = os.path.expanduser("~/.config/google-chrome")  # Update if necessary
    chrome_profile = "Profile 13"  # Change to your desired profile name, e.g., "Profile 1"

    chrome_options = uc.ChromeOptions()
    chrome_options.add_argument("--start-maximized")
    chrome_options.add_argument(f"--user-data-dir={chrome_user_data_dir}")
    chrome_options.add_argument(f"--profile-directory={chrome_profile}")
    chrome_options.add_argument("--no-sandbox")
    chrome_options.add_argument("--disable-dev-shm-usage")
    chrome_options.add_argument("--disable-extensions")
    chrome_options.add_argument("--disable-blink-features=AutomationControlled")
    # Optional: Run in headless mode
    # chrome_options.add_argument("--headless=new")

    try:
        driver = uc.Chrome(options=chrome_options, use_subprocess=True)
        logger.info("ChromeDriver initialized successfully.")
        return driver
    except Exception as e:
        logger.error(f"Failed to initialize ChromeDriver: {e}")
        logger.debug(traceback.format_exc())
        raise

# ----------------------------
# ChatGPT Automation Functions
# ----------------------------

@retry(max_attempts=3, delay=5, exceptions=(Exception,))
def navigate_to_chatgpt(driver):
    """
    Navigate to ChatGPT's website.
    """
    driver.get("https://chatgpt.com/c/67304f59-6040-8011-9fb5-78b1ff848349")
    logger.info("Navigated to ChatGPT.")

@retry(max_attempts=3, delay=5, exceptions=(Exception,))
def find_chat_input(wait):
    """
    Locate the chat input field.
    """
    chat_input_selector = "div[contenteditable='true']"
    logger.info("Waiting for chat input field to be clickable...")
    chat_input = wait.until(
        EC.element_to_be_clickable((By.CSS_SELECTOR, chat_input_selector))
    )
    logger.info("Chat input field is clickable.")
    return chat_input

@retry(max_attempts=3, delay=5, exceptions=(Exception,))
def send_message(driver, chat_input, message):
    """
    Send a message to ChatGPT.
    """
    actions = ActionChains(driver)
    actions.move_to_element(chat_input)
    actions.click()
    actions.send_keys(message)
    actions.send_keys(Keys.RETURN)
    actions.perform()
    logger.info(f"Typed and sent message: {message}")

@retry(max_attempts=3, delay=5, exceptions=(Exception,))
def get_response(wait, driver):
    """
    Retrieve the response from ChatGPT.
    """
    response_selector = "div.markdown.prose"
    logger.info("Waiting for response from ChatGPT...")
    wait.until(
        EC.presence_of_element_located((By.CSS_SELECTOR, response_selector))
    )
    # Wait for 10 seconds to ensure response is fully loaded
    time.sleep(10)
    responses = driver.find_elements(By.CSS_SELECTOR, response_selector)
    if not responses:
        raise Exception("No responses found.")
    response = responses[-1]  # Get the last response
    response_text = response.text
    logger.info(f"ChatGPT responded: {response_text}")
    return response_text

# ----------------------------
# Binance Configuration Parameters
# ----------------------------

LOGIN_URL = 'https://www.binance.com/en/login'
PROFILE_URL = 'https://www.binance.com/en/square'
POST_TEXT_FILE = 'chatgpt_response.txt'  # Updated to relative path since we'll avoid using absolute paths
# If you prefer absolute paths, ensure they are correct for your environment

# ----------------------------
# Helper Functions for Binance
# ----------------------------

def load_post_text(file_path):
    """Load post text from a specified file."""
    if not os.path.exists(file_path):
        logger.warning(f"Post text file not found at '{file_path}'. Using default text.")
        return "Default post text."

    with open(file_path, 'r') as file:
        content = file.read().strip()

    logger.info(f"Post text loaded from '{file_path}'.")
    return content

def paste_text(driver, element, text):
    """Paste text into the specified element using clipboard for faster insertion."""
    pyperclip.copy(text)
    element.click()
    if platform.system() == 'Darwin':
        element.send_keys(Keys.COMMAND, 'v')  # For macOS
    else:
        element.send_keys(Keys.CONTROL, 'v')  # For Windows/Linux
    logger.info(f"Pasted text into post editor.")

@retry(max_attempts=3, delay=5, exceptions=(Exception,))
def perform_posting(driver, post_text):
    """Automate the blog posting process."""
    wait = WebDriverWait(driver, 20)  # Increased timeout to 20 seconds

    try:
        # Navigate to the Profile Page
        driver.get(PROFILE_URL)
        logger.info(f"Navigated to profile page: {PROFILE_URL}")

        # Updated locator for the new <p> element
        # Replace with the correct XPath based on your inspection
        post_editor = wait.until(EC.element_to_be_clickable(
            (By.XPATH, "//p[contains(@class, 'selected') and @data-placeholder='Share your thoughts']")
        ))
        logger.info("Post editor is visible.")

        # Click on the editor to focus
        post_editor.click()

        # Clear existing text using JavaScript
        driver.execute_script("arguments[0].innerHTML = '';", post_editor)
        logger.info("Cleared existing text in the post editor.")

        # Insert the desired text using paste_text
        paste_text(driver, post_editor, post_text)

        # Click the 'Post' button
        post_button = wait.until(EC.element_to_be_clickable(
            (By.XPATH, "//button[@data-bn-type='button' and .//span[text()='Post']]")
        ))
        post_button.click()
        logger.info("Clicked the 'Post' button.")

    except Exception as e:
        logger.error(f"An error occurred during posting: {e}")
        logger.debug(traceback.format_exc())
        raise

# ----------------------------
# Cleanup Function
# ----------------------------

def cleanup(driver):
    """
    Cleanup resources such as the WebDriver.
    """
    if driver:
        driver.quit()
        logger.info("Browser closed during cleanup.")

# ----------------------------
# Main Execution Flow
# ----------------------------

def main():
    driver = None
    try:
        # Initialize WebDriver
        driver = initialize_driver()

        # ----------------------------
        # Phase 1: ChatGPT Automation
        # ----------------------------
        logger.info("\n=== Phase 1: ChatGPT Automation ===")
        navigate_to_chatgpt(driver)

        # Initialize WebDriverWait
        wait = WebDriverWait(driver, 60)  # Adjusted wait time

        chat_input = find_chat_input(wait)

        # Define your message
        message = (
            "good, this time give me other today news, can you compare you ensure and don't give me same news"
            "i need today date, crypto news for blog posting."
            "give me only news 2 news. without your talk."
            "on the right of the title add $BTC and second $ETH"
        )
        time.sleep(5)  # Reduced sleep time if possible
        send_message(driver, chat_input, message)

        # Wait for the response
        logger.info("Waiting for response from ChatGPT...")
        response_text = get_response(wait, driver)

        # Instead of writing to a file, we'll pass the response directly
        # However, if you still prefer to save it, uncomment the following lines:
        # with open(POST_TEXT_FILE, "w") as file:
        #     file.write(response_text)
        # logger.info(f"Response saved to {POST_TEXT_FILE}")

        # ----------------------------
        # Phase 2: Binance Posting
        # ----------------------------
        logger.info("\n=== Phase 2: Binance Automated Posting ===")

        # Option 1: Use the response_text directly
        post_text = response_text

        # Option 2: If you prefer to read from the file, ensure the previous write is uncommented
        # post_text = load_post_text(POST_TEXT_FILE)

        # Navigate to the LOGIN_URL
        logger.info(f"Navigating to LOGIN_URL: {LOGIN_URL}")
        driver.get(LOGIN_URL)
        logger.info(f"Navigated to {LOGIN_URL}")

        # Wait for the user to manually login if necessary
        # Adjust MANUAL_LOGIN_WAIT_TIME as needed
        MANUAL_LOGIN_WAIT_TIME = 1  # seconds
        logger.info(f"Waiting for {MANUAL_LOGIN_WAIT_TIME} seconds to ensure login session is active.")
        time.sleep(MANUAL_LOGIN_WAIT_TIME)

        # Perform the blog posting
        perform_posting(driver, post_text)

    except Exception as e:
        logger.error("An error occurred during the automation process:")
        logger.error(traceback.format_exc())
    finally:
        # Cleanup resources
        cleanup(driver)

# ----------------------------
# Entry Point
# ----------------------------

if __name__ == "__main__":
    main()
