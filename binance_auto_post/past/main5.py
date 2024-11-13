import time
import os
import platform
import pyperclip
import logging
import traceback
from functools import wraps
import undetected_chromedriver as uc
from selenium.webdriver.common.by import By
from selenium.webdriver.common.keys import Keys
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from selenium.common.exceptions import (
    TimeoutException,
    NoSuchElementException,
    ElementClickInterceptedException
)

# ----------------------------
# Configuration Parameters
# ----------------------------

# Binance URLs
LOGIN_URL = 'https://www.binance.com/en/login'
PROFILE_URL = 'https://www.binance.com/en/square'

# Time to wait after loading profile before posting
WAIT_AFTER_PROFILE_LOAD = 1  # seconds

# Path to the post text file
POST_TEXT_FILE = '/home/ethan/Documents/GitHub/TOY/binance_auto_post/chatgpt_response.txt'

# Time to wait for manual login (in seconds)
MANUAL_LOGIN_WAIT_TIME = 1  # Increased to 60 seconds

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s [%(levelname)s] %(message)s',
    handlers=[
        logging.FileHandler("binance_automation.log"),
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

    :param max_attempts: Maximum number of attempts.
    :param delay: Delay between attempts in seconds.
    :param exceptions: Tuple of exception classes to catch.
    :param on_failure: Optional callback function on final failure.
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
                    logger.warning(f"Attempt {attempts} failed with error: {e}")
                    if attempts < max_attempts:
                        logger.info(f"Retrying in {delay} seconds...")
                        time.sleep(delay)
                    else:
                        logger.error(f"All {max_attempts} attempts failed.")
                        if on_failure:
                            on_failure()
                        raise
        return wrapper
    return decorator

# ----------------------------
# Helper Functions
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
    logger.info(f"Pasted text into post editor: {text}")

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
    chrome_options.add_argument('--ignore-certificate-errors')
    chrome_options.add_argument('--ignore-ssl-errors')
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
# Main Execution Flow
# ----------------------------

def cleanup(driver):
    """
    Cleanup resources such as the WebDriver.
    """
    if driver:
        driver.quit()
        logger.info("Browser closed during cleanup.")

def main():
    driver = None
    try:
        driver = initialize_driver()

        # Since manual login is no longer required, skip login checks
        logger.info("=== Skipping Login Verification ===")
        logger.info("Waiting for 5 seconds before proceeding to post.")
        time.sleep(5)  # Wait for 5 seconds as per your requirement

        # Phase 2: Automated Blog Posting
        logger.info("\n=== Phase 2: Automated Blog Posting ===")

        # Load the post text from the file
        post_text = load_post_text(POST_TEXT_FILE)

        # Perform the blog posting
        perform_posting(driver, post_text)

    except Exception as e:
        logger.error("An unexpected error occurred in the main flow:")
        logger.error(traceback.format_exc())
    finally:
        # Close the browser after a short delay to observe the result
        if driver:
            time.sleep(5)
            cleanup(driver)

if __name__ == "__main__":
    main()
