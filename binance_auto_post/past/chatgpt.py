import os
import time
import traceback
import undetected_chromedriver as uc
import logging
from functools import wraps
from selenium.webdriver.common.by import By
from selenium.webdriver.common.keys import Keys
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s [%(levelname)s] %(message)s',
    handlers=[
        logging.FileHandler("chatgpt_automation.log"),
        logging.StreamHandler()
    ]
)
logger = logging.getLogger(__name__)

def retry(max_attempts=3, delay=5, exceptions=(Exception,)):
    """
    Decorator to retry a function upon encountering specified exceptions.

    :param max_attempts: Maximum number of attempts.
    :param delay: Delay between attempts in seconds.
    :param exceptions: Tuple of exception classes to catch.
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
                        raise
        return wrapper
    return decorator

@retry(max_attempts=3, delay=5, exceptions=(Exception,))
def initialize_driver():
    """
    Initialize the Chrome driver with specified options.
    """
    # Path to your existing Chrome user data directory
    chrome_user_data_dir = os.path.expanduser("~/.config/google-chrome")  # Update if necessary

    # Specify the profile directory you want to use
    chrome_profile = "Profile 13"  # Change if using another profile like "Profile 1"

    # Initialize Chrome options
    chrome_options = uc.ChromeOptions()
    chrome_options.add_argument("--start-maximized")
    chrome_options.add_argument(f"--user-data-dir={chrome_user_data_dir}")
    chrome_options.add_argument(f"--profile-directory={chrome_profile}")
    chrome_options.add_argument("--no-sandbox")
    chrome_options.add_argument("--disable-dev-shm-usage")
    # Uncomment if needed
    # chrome_options.add_argument("--remote-debugging-port=9222")
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
        traceback_str = traceback.format_exc()
        logger.error(traceback_str)
        raise

@retry(max_attempts=3, delay=5, exceptions=(Exception,))
def navigate_to_chatgpt(driver):
    """
    Navigate to ChatGPT's website.
    """
    driver.get("https://chat.openai.com/")
    logger.info("Navigated to ChatGPT.")

@retry(max_attempts=3, delay=5, exceptions=(Exception,))
def find_chat_input(wait):
    """
    Locate the chat input field.
    """
    chat_input_selector = "textarea[placeholder='Send a message']"
    logger.info("Waiting for chat input field to be clickable...")
    chat_input = wait.until(
        EC.element_to_be_clickable((By.CSS_SELECTOR, chat_input_selector))
    )
    logger.info("Chat input field is clickable.")
    return chat_input

@retry(max_attempts=3, delay=5, exceptions=(Exception,))
def send_message(chat_input, message):
    """
    Send a message to ChatGPT.
    """
    chat_input.click()
    logger.info("Clicked on chat input field.")
    chat_input.send_keys(message)
    logger.info(f"Typed message: {message}")
    chat_input.send_keys(Keys.ENTER)
    logger.info("Message sent. Waiting for response...")

@retry(max_attempts=3, delay=5, exceptions=(Exception,))
def get_response(wait):
    """
    Retrieve the response from ChatGPT.
    """
    response_selector = "div.markdown.prose:last-child"
    response = wait.until(
        EC.presence_of_element_located((By.CSS_SELECTOR, response_selector))
    )
    logger.info("Response received.")
    response_text = response.text
    logger.info(f"ChatGPT responded: {response_text}")
    return response_text

def main():
    driver = None
    try:
        driver = initialize_driver()
        navigate_to_chatgpt(driver)

        # Initialize WebDriverWait
        wait = WebDriverWait(driver, 60)  # Adjusted wait time

        chat_input = find_chat_input(wait)

        # Define your message
        message = "Hello, ChatGPT! How can you assist me today?"

        send_message(chat_input, message)

        response_text = get_response(wait)

    except Exception as e:
        logger.error("An error occurred during automation:")
        traceback_str = traceback.format_exc()
        logger.error(traceback_str)
    finally:
        if driver:
            driver.quit()
            logger.info("Browser closed.")

if __name__ == "__main__":
    main()