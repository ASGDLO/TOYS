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
from selenium.common.exceptions import TimeoutException, NoSuchElementException
import requests

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s [%(levelname)s] %(message)s',
    handlers=[
        logging.FileHandler("chatgpt_automation.log"),
        logging.StreamHandler()
    ]
)
os.system("pkill chrome")
logger = logging.getLogger(__name__)



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

        
def navigate_to_chatgpt(driver):
    """
    Navigate to ChatGPT's website.
    """
    driver.get("https://chatgpt.com/c/673149f4-db6c-8011-8ee2-0a976544dd20")
    logger.info("Navigated to ChatGPT.")


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


def search_google_and_save_image(driver, search_query):
    """
    Search Google Images with the given query, type the query in the search box, and save a screenshot named Unlimited.png.
    """
    # Navigate to Google Images
    driver.get("https://images.google.com/")
    logger.info("Navigated to Google Images.")

    wait = WebDriverWait(driver, 20)

    try:

        # Locate the search input field
        search_input = wait.until(
            EC.presence_of_element_located((By.NAME, "q"))
        )
        logger.info("Google Images search input located.")

        # Clear the input field and type the search query
        search_input.clear()
        search_input.send_keys(search_query)
        search_input.send_keys(Keys.RETURN)
        logger.info(f"Typed and submitted search query: {search_query}")

        # Wait for the search results to load
        wait.until(
            EC.presence_of_element_located((By.CSS_SELECTOR, "div#search"))
        )
        logger.info("Search results loaded.")

        # Optional: Scroll to the bottom to ensure all images are loaded
        driver.execute_script("window.scrollTo(0, document.body.scrollHeight);")
        time.sleep(2)  # Wait for scrolling

        # Capture the screenshot of the entire page
        screenshot_path = "Unlimited.png"
                # Set device pixel ratio to 1
        driver.execute_script("window.devicePixelRatio = 1")
        logger.info("Set device pixel ratio to 1.")

        # Set zoom level to 100%
        driver.execute_script("document.body.style.zoom='300%'")
        logger.info("Set browser zoom level to 100%.")

        driver.save_screenshot(screenshot_path)
        logger.info(f"Screenshot saved as {screenshot_path}")

    except Exception as e:
        logger.error(f"Failed to search and save image: {e}")
        traceback_str = traceback.format_exc()
        logger.error(traceback_str)
        raise

def cleanup(driver):
    """
    Cleanup resources such as the WebDriver.
    """
    if driver:
        driver.quit()
        logger.info("Browser closed during cleanup.")

def sanitize_filename(name):
    """
    Sanitize the search query to create a safe filename.
    """
    return "".join(c if c.isalnum() else "_" for c in name)

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
            "this time give me other news, can you compare you ensure and don't give me same news, cryptocurrency news for blog posting. give me only one news. without your talk. summarize. add emoji"
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

        # Extract the title from the response text for Google search
        title = response_text.split('\n')[0]  # Assuming the title is the first line
        logger.info(f"Extracted title for image search: {title}")

        # Search Google Images and save the screenshot
        search_google_and_save_image(driver, title)

    except Exception as e:
        logger.error("An error occurred during automation:")
        traceback_str = traceback.format_exc()
        logger.error(traceback_str)
        raise
    finally:
        cleanup(driver)

if __name__ == "__main__":
    main()
