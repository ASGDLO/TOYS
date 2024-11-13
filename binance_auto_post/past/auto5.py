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
import subprocess  # Import for subprocess execution

# ----------------------------
# Configuration Parameters
# ----------------------------

# Path to main3.py
MAIN3_PATH = "/home/ethan/Documents/GitHub/TOY/binance_auto_post/main3.py"

# Loop interval in seconds (5 minutes)
LOOP_INTERVAL = 5 * 60  # 300 seconds

# ----------------------------
# Configure Logging
# ----------------------------

logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s [%(levelname)s] %(message)s',
    handlers=[
        logging.FileHandler("chatgpt_automation.log"),
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
# Primary Functions
# ----------------------------

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

def execute_main3():
    """
    Execute main3.py as a subprocess.
    """
    logger.info("Executing main3.py...")
    
    # Ensure the path exists
    if not os.path.isfile(MAIN3_PATH):
        logger.error(f"main3.py not found at {MAIN3_PATH}")
        return False

    try:
        # Run main3.py using the same Python interpreter
        result = subprocess.run([sys.executable, MAIN3_PATH], capture_output=True, text=True)
        
        # Check if main3.py ran successfully
        if result.returncode == 0:
            logger.info("main3.py executed successfully.")
            logger.debug(f"main3.py Output:\n{result.stdout}")
            return True
        else:
            logger.error("main3.py execution failed.")
            logger.error(f"main3.py Error Output:\n{result.stderr}")
            return False
    except Exception as e:
        logger.error(f"Failed to execute main3.py: {e}")
        traceback_str = traceback.format_exc()
        logger.error(traceback_str)
        return False

# ----------------------------
# Main Process Function
# ----------------------------

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
        
        # Execute main3.py After Completion
        success = execute_main3()
        if not success:
            logger.error("main3.py did not execute successfully.")
            # Depending on your requirements, you can choose to raise an exception here
            # raise Exception("main3.py execution failed.")
        
    except Exception as e:
        logger.error("An error occurred during automation:")
        traceback_str = traceback.format_exc()
        logger.error(traceback_str)
        raise
    finally:
        cleanup(driver)

# ----------------------------
# Looping Mechanism
# ----------------------------

def run_process():
    """
    Runs the main process and handles any exceptions to ensure the loop continues.
    """
    logger.info("=== Starting New Iteration ===")
    start_time = time.time()
    try:
        main()
    except Exception as e:
        logger.error(f"Process encountered an error: {e}")
    end_time = time.time()
    elapsed = end_time - start_time
    logger.info(f"=== Iteration Completed in {elapsed:.2f} seconds ===\n")

def loop_every(interval_seconds):
    """
    Runs the run_process function every `interval_seconds` seconds.
    """
    while True:
        run_process()
        logger.info(f"Sleeping for {interval_seconds} seconds before next iteration.\n")
        time.sleep(interval_seconds)

# ----------------------------
# Entry Point
# ----------------------------

if __name__ == "__main__":
    try:
        logger.info("=== Automation Script Started ===")
        loop_every(LOOP_INTERVAL)
    except KeyboardInterrupt:
        logger.info("Automation script terminated by user.")
    except Exception as e:
        logger.error(f"Unhandled exception: {e}")
        traceback_str = traceback.format_exc()
        logger.error(traceback_str)
