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
import subprocess  # New import for subprocess execution

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
    driver.get("https://chatgpt.com/c/672ddc5f-445c-8011-b908-3b839086ff96")
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
        message = (
            "good, this time give me other today news, can you compare you ensure and don't give me same news. "
            "I need today's date, crypto news for blog posting. "
            "Give me only 2 news items without your talk. "
            "Add $BTC $ETH."
        )
        time.sleep(5)  # Reduced sleep time if possible
        send_message(driver, chat_input, message)

        # Wait for the response
        logger.info("Waiting for response...")
        response_text = get_response(wait, driver)

        # Store the response as needed
        with open("chatgpt_response.txt", "w") as file:
            file.write(response_text)
        logger.info("Response saved to chatgpt_response.txt")
        
        # ----------------------------
        # Execute main3.py After Completion
        # ----------------------------
        logger.info("Executing main3.py...")
        main3_path = "/home/ethan/Documents/GitHub/TOY/binance_auto_post/main3.py"
        
        # Ensure the path exists
        if not os.path.isfile(main3_path):
            logger.error(f"main3.py not found at {main3_path}")
            sys.exit(1)
        
        # Run main3.py using the same Python interpreter
        result = subprocess.run([sys.executable, main3_path], capture_output=True, text=True)
        
        # Check if main3.py ran successfully
        if result.returncode == 0:
            logger.info("main3.py executed successfully.")
            logger.debug(f"main3.py Output:\n{result.stdout}")
        else:
            logger.error("main3.py execution failed.")
            logger.error(f"main3.py Error Output:\n{result.stderr}")
            sys.exit(result.returncode)

    except Exception as e:
        logger.error("An error occurred during automation:")
        traceback_str = traceback.format_exc()
        logger.error(traceback_str)
        raise
    finally:
        cleanup(driver)

if __name__ == "__main__":
    main()
