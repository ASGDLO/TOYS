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
from selenium.webdriver.common.action_chains import ActionChains
import sys
from selenium.common.exceptions import (
    TimeoutException,
    NoSuchElementException,
    ElementClickInterceptedException
)

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

@retry(max_attempts=3, delay=5, exceptions=(Exception,))
def initialize_driver():
    """
    Initialize the Chrome driver with specified options.
    """
    chrome_user_data_dir = os.path.expanduser("~/.config/google-chrome")  # Update if necessary
    chrome_profile = "Profile 13"  # Change if using another profile like "Profile 1"

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

def cleanup(driver):
    """
    Cleanup resources such as the WebDriver.
    """
    if driver:
        driver.quit()
        logger.info("Browser closed during cleanup.")

def perform_posting(driver, post_text):
    """Automate the blog posting process."""
    wait = WebDriverWait(driver, 60)  # Increased timeout to 60 seconds
    LOGIN_URL = 'https://www.binance.com/en/login'
    PROFILE_URL = 'https://www.binance.com/en/square'

    try:
        # Navigate to the Login Page first
        driver.get(LOGIN_URL)
        logger.info(f"Navigated to login page: {LOGIN_URL}")
        logger.info("Please log in manually.")

        # Wait for the user to log in (adjust time as needed)
        time.sleep(1)  # Wait for 60 seconds for manual login

        # Navigate to the profile page after login
        driver.get(PROFILE_URL)
        logger.info(f"Navigated to profile page: {PROFILE_URL}")

        # Wait for the post editor to be present
        post_editor_xpath = "//p[contains(@class, 'selected') and @data-placeholder='Share your thoughts']"
        post_editor = wait.until(EC.element_to_be_clickable(
            (By.XPATH, post_editor_xpath)
        ))
        logger.info("Post editor is visible.")

        # Click on the editor to focus
        post_editor.click()
        logger.info("Clicked on the post editor to focus.")

        # Clear existing text using JavaScript
        driver.execute_script("arguments[0].innerHTML = '';", post_editor)
        logger.info("Cleared existing text in the post editor.")

        # Insert the desired text using send_keys
        post_editor.send_keys(post_text)
        logger.info(f"Inserted text into post editor: {post_text}")

        # Click the 'Post' button
        post_button_xpath = "//button[@data-bn-type='button' and .//span[text()='Post']]"
        post_button = wait.until(EC.element_to_be_clickable(
            (By.XPATH, post_button_xpath)
        ))
        post_button.click()
        logger.info("Clicked the 'Post' button.")

    except Exception as e:
        logger.error(f"An error occurred during posting: {e}")
        traceback_str = traceback.format_exc()
        logger.error(traceback_str)
        raise

@retry(max_attempts=5, delay=10, exceptions=(Exception,), on_failure=lambda: sys.exit(1))
def main():
    driver = None
    try:
        driver = initialize_driver()
        navigate_to_chatgpt(driver)

        # Initialize WebDriverWait
        wait = WebDriverWait(driver, 60)  # Adjusted wait time

        chat_input = find_chat_input(wait)

        # Define your message
        message = "I need BTC and ETH news, without your personal talk, only news."
        time.sleep(5)  # Reduced sleep time if possible
        send_message(driver, chat_input, message)

        # Wait for the response
        logger.info("Waiting for response...")
        response_text = get_response(wait, driver)

        # Store the response as needed
        with open("chatgpt_response.txt", "w") as file:
            file.write(response_text)
        logger.info("Response saved to chatgpt_response.txt")

        # Now, proceed to perform the posting
        perform_posting(driver, response_text)
        logger.info("Posting completed.")

    except Exception as e:
        logger.error("An error occurred during automation:")
        traceback_str = traceback.format_exc()
        logger.error(traceback_str)
        raise
    finally:
        cleanup(driver)

if __name__ == "__main__":
    main()
