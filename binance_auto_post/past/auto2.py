import os
import time
import json
import traceback
import logging
import sys
from functools import wraps

import undetected_chromedriver as uc
from selenium import webdriver
from selenium.webdriver.chrome.service import Service as ChromeService
from selenium.webdriver.chrome.options import Options
from selenium.webdriver.common.by import By
from selenium.webdriver.common.keys import Keys  # Make sure to import Keys if you're using it
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
        logging.FileHandler("combined_automation.log"),
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
# ChatGPT Automation Class
# ----------------------------
class ChatGPTAutomation:
    def __init__(self):
        self.chatgpt_response_file = "chatgpt_response.txt"

    @retry(max_attempts=3, delay=5, exceptions=(Exception,))
    def initialize_driver(self):
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
            logger.info("ChatGPT ChromeDriver initialized successfully.")
            return driver
        except Exception as e:
            logger.error(f"Failed to initialize ChatGPT ChromeDriver: {e}")
            traceback_str = traceback.format_exc()
            logger.error(traceback_str)
            raise

    @retry(max_attempts=3, delay=5, exceptions=(Exception,))
    def navigate_to_chatgpt(self, driver):
        """
        Navigate to ChatGPT's website.
        """
        chatgpt_url = "https://chatgpt.com/c/672ddc5f-445c-8011-b908-3b839086ff96"  # Update as needed
        driver.get(chatgpt_url)
        logger.info("Navigated to ChatGPT.")

    @retry(max_attempts=3, delay=5, exceptions=(Exception,))
    def find_chat_input(self, wait):
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
    def send_message(self, driver, chat_input, message):
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
    def get_response(self, wait, driver):
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

    def cleanup(self, driver):
        """
        Cleanup resources such as the WebDriver.
        """
        if driver:
            driver.quit()
            logger.info("ChatGPT Browser closed during cleanup.")

    def run(self):
        """
        Execute the ChatGPT automation process.
        """
        driver = None
        try:
            driver = self.initialize_driver()
            self.navigate_to_chatgpt(driver)

            # Initialize WebDriverWait
            wait = WebDriverWait(driver, 60)  # Adjusted wait time

            chat_input = self.find_chat_input(wait)

            # Define your message
            message = "I need BTC and ETH news, without personal talk, only news."
            time.sleep(5)  # Reduced sleep time if possible
            self.send_message(driver, chat_input, message)

            # Wait for the response
            logger.info("Waiting for response...")
            response_text = self.get_response(wait, driver)

            # Store the response
            with open(self.chatgpt_response_file, "w") as file:
                file.write(response_text)
            logger.info(f"Response saved to {self.chatgpt_response_file}")

        except Exception as e:
            logger.error("An error occurred during ChatGPT automation:")
            traceback_str = traceback.format_exc()
            logger.error(traceback_str)
            raise
        finally:
            self.cleanup(driver)

# ----------------------------
# Binance Automation Class
# ----------------------------
class BinanceAutomation:
    def __init__(self):
        self.cookies_path = 'cookies.json'
        self.local_storage_path = 'local_storage.json'
        self.login_url = 'https://www.binance.com/en/login'
        self.profile_url = 'https://www.binance.com/en/square'
        self.post_text = self.load_chatgpt_response()
        self.manual_login_wait_time = 10  # seconds
        self.wait_after_extraction = 10  # seconds
        self.chrome_driver_path = '/usr/local/bin/chromedriver'  # Update as needed

    def load_chatgpt_response(self):
        """
        Load the ChatGPT response from the text file.
        """
        if not os.path.exists("chatgpt_response.txt"):
            logger.error("chatgpt_response.txt not found. Ensure ChatGPT automation ran successfully.")
            sys.exit(1)
        with open("chatgpt_response.txt", "r") as file:
            response = file.read().strip()
        logger.info("Loaded ChatGPT response for posting.")
        return response

    def save_cookies(self, driver, path):
        """Save cookies to a JSON file."""
        cookies = driver.get_cookies()
        with open(path, 'w') as file:
            json.dump(cookies, file)
        logger.info(f"Cookies have been saved to '{path}'.")

    def save_local_storage(self, driver, path):
        """Save local storage to a JSON file."""
        local_storage = driver.execute_script("return window.localStorage;")
        with open(path, 'w') as file:
            json.dump(local_storage, file)
        logger.info(f"Local storage has been saved to '{path}'.")

    def load_cookies(self, driver, path):
        """Load cookies from a JSON file into the browser."""
        if not os.path.exists(path):
            logger.warning(f"No cookies file found at '{path}'. Skipping cookie loading.")
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
                logger.error(f"Error adding cookie {cookie}: {e}")
        logger.info("Cookies loaded successfully.")

    def load_local_storage(self, driver, path):
        """Load local storage from a JSON file into the browser."""
        if not os.path.exists(path):
            logger.warning(f"No local storage file found at '{path}'. Skipping local storage loading.")
            return
        with open(path, 'r') as file:
            local_storage = json.load(file)
        for key, value in local_storage.items():
            # Sanitize the value to prevent JavaScript injection
            sanitized_value = value.replace("'", "\\'").replace('"', '\\"')
            script = f"window.localStorage.setItem('{key}', '{sanitized_value}');"
            driver.execute_script(script)
        logger.info("Local storage loaded successfully.")

    def perform_posting(self, driver, post_text):
        """Automate the blog posting process."""
        wait = WebDriverWait(driver, 30)  # Increased timeout to 30 seconds

        try:
            # Navigate to the Profile Page
            driver.get(self.profile_url)
            logger.info(f"Navigated to profile page: {self.profile_url}")

            # Updated locator for the new <p> element
            post_editor = wait.until(EC.element_to_be_clickable(
                (By.XPATH, "//p[contains(@class, 'selected') and @data-placeholder='Share your thoughts']")
            ))
            logger.info("Post editor is visible.")

            # Click on the editor to focus
            post_editor.click()

            # Clear existing text using JavaScript
            driver.execute_script("arguments[0].innerHTML = '';", post_editor)
            logger.info("Cleared existing text in the post editor.")

            # Insert the desired text using send_keys
            post_editor.send_keys(post_text)
            logger.info(f"Inserted text into post editor: {post_text}")

            # Click the 'Post' button
            post_button = wait.until(EC.element_to_be_clickable(
                (By.XPATH, "//button[@data-bn-type='button' and .//span[text()='Post']]")
            ))
            post_button.click()
            logger.info("Clicked the 'Post' button.")

        except Exception as e:
            logger.error(f"An error occurred during posting: {e}")
            traceback_str = traceback.format_exc()
            logger.error(traceback_str)
            raise

    @retry(max_attempts=3, delay=5, exceptions=(Exception,))
    def initialize_webdriver(self):
        """
        Initialize the Chrome WebDriver with specified options.
        """
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

        try:
            service = ChromeService(executable_path=self.chrome_driver_path)
            driver = webdriver.Chrome(service=service, options=chrome_options)
            logger.info("Binance ChromeDriver initialized successfully.")
            return driver
        except Exception as e:
            logger.error(f"Failed to initialize Binance ChromeDriver: {e}")
            traceback_str = traceback.format_exc()
            logger.error(traceback_str)
            raise

    def cleanup(self, driver):
        """
        Cleanup resources such as the WebDriver.
        """
        if driver:
            driver.quit()
            logger.info("Binance Browser closed during cleanup.")

    def run(self):
        """
        Execute the Binance automation process.
        """
        driver = None
        try:
            driver = self.initialize_webdriver()
            
            # Phase 1: Manual Login and Extraction
            logger.info("=== Phase 1: Manual Login and Extraction ===")
            driver.get(self.login_url)
            logger.info(f"Navigated to {self.login_url}")
            logger.info(f"Please log in manually within the next {self.manual_login_wait_time} seconds.")
            time.sleep(self.manual_login_wait_time)  # Wait for manual login

            # After login, save cookies and local storage
            self.save_cookies(driver, self.cookies_path)
            self.save_local_storage(driver, self.local_storage_path)

            # Phase 2: Automated Blog Posting
            logger.info("\n=== Phase 2: Automated Blog Posting ===")
            logger.info(f"Waiting for {self.wait_after_extraction} seconds before proceeding to post.")
            time.sleep(self.wait_after_extraction)

            # Reload the page to ensure cookies and local storage are applied
            driver.refresh()
            logger.info("Page refreshed to apply authentication.")

            # Perform the blog posting
            self.perform_posting(driver, self.post_text)

        except Exception as e:
            logger.error("An error occurred during Binance automation:")
            traceback_str = traceback.format_exc()
            logger.error(traceback_str)
            raise
        finally:
            self.cleanup(driver)

# ----------------------------
# Combined Automation Class
# ----------------------------
class CombinedAutomation:
    def __init__(self):
        self.chatgpt_automation = ChatGPTAutomation()
        self.binance_automation = BinanceAutomation()

    def run(self):
        """
        Execute the combined automation process: ChatGPT followed by Binance.
        """
        logger.info("=== Starting Combined Automation ===")
        # Step 1: Run ChatGPT Automation
        logger.info("=== Step 1: ChatGPT Automation ===")
        self.chatgpt_automation.run()

        # Step 2: Run Binance Automation
        logger.info("=== Step 2: Binance Automation ===")
        self.binance_automation.run()

        logger.info("=== Combined Automation Completed Successfully ===")

# ----------------------------
# Main Execution
# ----------------------------
if __name__ == "__main__":
    combined = CombinedAutomation()
    combined.run()