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

# Path to the image file to be posted
IMAGE_PATH = '/home/ethan/Documents/GitHub/TOY/binance_auto_post/Unlimited.png'

# Time to wait for manual login (in seconds)
MANUAL_LOGIN_WAIT_TIME = 5  # Updated to 5 seconds

# Configure logging
logging.basicConfig(
    level=logging.DEBUG,  # Changed to DEBUG for detailed logs
    format='%(asctime)s [%(levelname)s] %(message)s',
    handlers=[
        logging.FileHandler("binance_automation.log"),
        logging.StreamHandler()
    ]
)
logger = logging.getLogger(__name__)

# Kill all existing Chrome processes
os.system("pkill chrome")
logger.info("Terminated all existing Chrome processes.")

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

def upload_image(driver, image_path):
    """Upload an image to the post editor by interacting with the upload button and file input."""
    try:
        if not os.path.isfile(image_path):
            logger.error(f"Image file not found at '{image_path}'.")
            return

        wait = WebDriverWait(driver, 30)

        # Locate the upload container
        upload_container = wait.until(
            EC.presence_of_element_located(
                (By.XPATH, '//*[@id="shortPostEditorImageUploaderBox"]')
            )
        )
        logger.info("Upload container located.")

        # Locate the file input within the upload container
        try:
            # Attempt using XPath
            file_input = upload_container.find_element(By.XPATH, './/input[@type="file"]')
            logger.info("File input element located within the upload container via XPath.")
        except NoSuchElementException:
            # Fallback to CSS Selector if XPath fails
            file_input = upload_container.find_element(By.CSS_SELECTOR, 'input[type="file"]')
            logger.info("File input element located within the upload container via CSS Selector.")

        # Make the file input visible if it's hidden
        driver.execute_script("arguments[0].style.display = 'block';", file_input)
        logger.debug("Removed 'display: none' style from the file input.")

        # Send the absolute image path to the file input
        absolute_image_path = os.path.abspath(image_path)
        file_input.send_keys(absolute_image_path)
        logger.info(f"Image path '{absolute_image_path}' sent to file input.")

        # Trigger a change event if necessary
        driver.execute_script("arguments[0].dispatchEvent(new Event('change'));", file_input)
        logger.debug("Triggered change event on the file input.")

        # Wait for the image to be uploaded/displayed
        uploaded_image_xpath = f"//img[contains(@src, '{os.path.splitext(os.path.basename(image_path))[0]}')]"
        try:
            uploaded_image = wait.until(
                EC.presence_of_element_located(
                    (By.XPATH, uploaded_image_xpath)
                )
            )
            logger.info("Image uploaded successfully.")
        except TimeoutException:
            logger.error("Uploaded image not found in the DOM.")

    except TimeoutException:
        logger.error("Timeout while trying to upload image.")
        logger.debug(traceback.format_exc())
    except Exception as e:
        logger.error(f"An error occurred during image upload: {e}")
        logger.debug(traceback.format_exc())

def perform_posting(driver, post_text):
    """Automate the blog posting process, including text and image."""
    wait = WebDriverWait(driver, 30)  # Increased timeout for reliability

    try:
        # Navigate to the Profile Page
        driver.get(PROFILE_URL)
        logger.info(f"Navigated to profile page: {PROFILE_URL}")

        # Locate the post editor
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

        # Upload the image
        upload_image(driver, IMAGE_PATH)

        # ----------------------------
        # Added Delay After Uploading Image
        # ----------------------------
        logger.info("Waiting for 5 seconds after uploading image to allow processing.")
        time.sleep(5)  # Wait for 5 seconds
        logger.debug("Waited for 5 seconds.")
        # ----------------------------

        # ----------------------------
        # Added Sequential Click Actions
        # ----------------------------
        # List of XPaths to click in sequence
        additional_click_xpaths = [
            '//*[@id="feed-home-tabs"]/div[1]/div[1]/div[1]/div[1]/div[2]/div[2]/div[1]/div/div[1]/div/div[5]',
            '//*[@id="tippy-7"]/div/div[2]/div[2]',
            '//*[@id="feed-home-tabs"]/div[1]/div[1]/div[1]/div[1]/div[2]/div[2]/div[1]/div/div[1]/div/div[5]',
            '//*[@id="tippy-7"]/div/div[2]/div[2]',
            '//*[@id="post-editor-more-icon"]/div[1]',
            '//*[@id="tippy-9"]/div/div[1]'
        ]

        for index, xpath in enumerate(additional_click_xpaths, start=1):
            try:
                logger.info(f"Attempting to locate and click element {index} with XPath: {xpath}")
                element = wait.until(EC.element_to_be_clickable((By.XPATH, xpath)))
                element.click()
                logger.info(f"Clicked element {index} successfully.")
                time.sleep(2)  # Wait for 2 seconds between clicks
            except TimeoutException:
                logger.error(f"Timeout while trying to locate element {index} with XPath: {xpath}")
            except Exception as e:
                logger.error(f"An error occurred while clicking element {index}: {e}")
        # ----------------------------
        time.sleep(5)
        # Click the 'Post' button
        post_button = wait.until(EC.element_to_be_clickable(
            (By.XPATH, "//button[@data-bn-type='button' and .//span[text()='Post']]")
        ))
        post_button.click()
        logger.info("Clicked the 'Post' button.")

        # Added Delay After Clicking Post
        logger.info("Waiting for 1 second after clicking 'Post' to allow processing.")
        time.sleep(1)  # Wait for 1 second
        logger.debug("Waited for 1 second.")

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

        # Navigate to the LOGIN_URL
        logger.info(f"Navigating to LOGIN_URL: {LOGIN_URL}")
        driver.get(LOGIN_URL)
        logger.info(f"Navigated to {LOGIN_URL}")

        # Wait for manual login
        logger.info(f"Waiting for {MANUAL_LOGIN_WAIT_TIME} seconds for manual login.")
        time.sleep(MANUAL_LOGIN_WAIT_TIME)

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
