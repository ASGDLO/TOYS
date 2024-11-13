import json
import os
import time
from selenium import webdriver
from selenium.webdriver.common.by import By
from selenium.webdriver.chrome.service import Service as ChromeService
from selenium.webdriver.chrome.options import Options
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from dotenv import load_dotenv

# Load environment variables from .env file (if using for credentials)
load_dotenv()

# Retrieve credentials from environment variables
BINANCE_USERNAME = os.getenv('BINANCE_USERNAME')
BINANCE_PASSWORD = os.getenv('BINANCE_PASSWORD')

# Paths to your ChromeDriver and data files
CHROME_DRIVER_PATH = '/usr/local/bin/chromedriver'  # Update this path as needed
COOKIES_FILE = 'cookies.json'
STORAGE_FILE = 'local_storage.json'

def save_cookies_and_storage(driver, cookies_file, storage_file):
    """
    Save cookies and local storage from the browser into specified JSON files.
    """
    try:
        # Save Cookies
        cookies = driver.get_cookies()
        with open(cookies_file, 'w') as file:
            json.dump(cookies, file)
        print("Cookies saved successfully.")
    except Exception as e:
        print(f"Failed to save cookies: {e}")

    try:
        # Save Local Storage
        local_storage = driver.execute_script("return window.localStorage;")
        with open(storage_file, 'w') as file:
            json.dump(local_storage, file)
        print("Local storage saved successfully.")
    except Exception as e:
        print(f"Failed to save local storage: {e}")

def load_cookies_and_storage(driver, cookies_file, storage_file):
    """
    Load cookies and local storage from specified JSON files into the browser.
    """
    try:
        # Load Cookies
        with open(cookies_file, 'r') as file:
            cookies = json.load(file)
            for cookie in cookies:
                # Selenium requires 'expiry' to be an integer
                if 'expiry' in cookie:
                    cookie['expiry'] = int(cookie['expiry'])
                # Remove 'sameSite' attribute if present, as Selenium might not accept it
                cookie.pop('sameSite', None)
                driver.add_cookie(cookie)
        print("Cookies loaded successfully.")
    except Exception as e:
        print(f"Failed to load cookies: {e}")

    try:
        # Load Local Storage
        with open(storage_file, 'r') as file:
            local_storage = json.load(file)
            for key, value in local_storage.items():
                # Ensure proper escaping of quotes in keys and values
                safe_key = key.replace("'", "\\'")
                safe_value = value.replace("'", "\\'")
                driver.execute_script(f"window.localStorage.setItem('{safe_key}', '{safe_value}');")
        print("Local storage loaded successfully.")
    except Exception as e:
        print(f"Failed to load local storage: {e}")

def is_logged_in(driver):
    """
    Check if the user is logged in by looking for a user-specific element.
    Adjust the XPath based on Binance's actual user interface.
    """
    try:
        # Example: Look for a profile icon or user-specific element
        driver.find_element(By.XPATH, '//div[contains(@class, "user-info")]')
        return True
    except:
        return False

def perform_login(driver, wait):
    """
    Automate the login process by entering credentials.
    """
    try:
        # Navigate to Login Page
        driver.get("https://www.binance.com/en/login")
        print("Navigated to Binance login page.")

        # Maximize window
        driver.maximize_window()

        # Enter Username
        username_field = wait.until(EC.presence_of_element_located((By.ID, 'email')))
        username_field.clear()
        username_field.send_keys(BINANCE_USERNAME)
        print("Entered username.")

        # Enter Password
        password_field = driver.find_element(By.ID, 'password')
        password_field.clear()
        password_field.send_keys(BINANCE_PASSWORD)
        print("Entered password.")

        # Click Login Button
        login_button = driver.find_element(By.XPATH, '//button[contains(text(), "Log In")]')
        login_button.click()
        print("Clicked the 'Log In' button.")

        # Handle Two-Factor Authentication (If Enabled)
        try:
            # Wait for 2FA input to appear
            auth_input = wait.until(EC.presence_of_element_located((By.ID, 'authCode')))
            # Prompt user to enter 2FA code manually
            auth_code = input("Enter your 2FA code: ")
            auth_input.send_keys(auth_code)
            print("Entered 2FA code.")

            # Click Verify Button
            verify_button = driver.find_element(By.XPATH, '//button[contains(text(), "Verify")]')
            verify_button.click()
            print("Clicked the 'Verify' button for 2FA.")
        except:
            print("Two-Factor Authentication (2FA) not detected or already handled.")

        # Wait until logged in by checking for user-specific element
        wait.until(EC.presence_of_element_located((By.XPATH, '//div[contains(@class, "user-info")]')))
        print("Logged in successfully.")

    except Exception as e:
        print(f"An error occurred during login: {e}")
        raise  # Re-raise the exception to be handled by the outer try-except

def automate_blog_post():
    # Initialize Chrome options
    chrome_options = Options()
    # Optional: Run Chrome in headless mode
    # chrome_options.add_argument('--headless')
    # Optional: Disable notifications
    chrome_options.add_argument("--disable-notifications")
    # Optional: Use a specific user data directory
    # chrome_options.add_argument("user-data-dir=/path/to/your/chrome/profile")

    # Initialize the Chrome WebDriver
    service = ChromeService(executable_path=CHROME_DRIVER_PATH)
    driver = webdriver.Chrome(service=service, options=chrome_options)

    # Define an explicit wait
    wait = WebDriverWait(driver, 20)  # 20 seconds timeout

    try:
        # Step 1: Open the Binance Login Page
        driver.get("https://www.binance.com/en/login")
        print("Opened Binance login page.")

        # Maximize window
        driver.maximize_window()

        # Step 2: Load cookies and local storage (if available)
        if os.path.exists(COOKIES_FILE) and os.path.exists(STORAGE_FILE):
            load_cookies_and_storage(driver, COOKIES_FILE, STORAGE_FILE)
            driver.refresh()
            print("Loaded cookies and local storage.")
            time.sleep(5)  # Wait for session to apply
        else:
            print("No existing cookies found. Proceeding to manual login.")

        # Step 3: Check if logged in
        if not is_logged_in(driver):
            print("Not logged in. Initiating login process.")
            perform_login(driver, wait)
            # Save cookies and local storage after successful login
            save_cookies_and_storage(driver, COOKIES_FILE, STORAGE_FILE)
        else:
            print("Already logged in. Proceeding to blog posting.")

        # Step 4: Navigate to the Square Creator Profile
        target_url = "https://www.binance.com/en/square/profile/Square-Creator-b82001242"
        driver.get(target_url)
        print(f"Navigated to {target_url}")
        time.sleep(5)  # Wait for the page to load

        # Step 5: Click the "Post" Button to Open the Editor
        try:
            post_button = wait.until(EC.element_to_be_clickable((By.XPATH, '//button[contains(text(), "Post")]')))
            post_button.click()
            print("Clicked the 'Post' button to open the editor.")
        except Exception as e:
            print(f"Failed to locate or click the 'Post' button: {e}")
            return  # Exit the function or handle as needed

        # Step 6: Enter Text into the Post Editor
        try:
            # Locate the <p> tag with specific attributes
            post_editor = wait.until(EC.presence_of_element_located((
                By.XPATH, '//p[@data-placeholder="Share your thoughts" and contains(@class, "is-editor-empty")]'
            )))
            post_editor.click()  # Focus on the editor
            post_editor.send_keys("hello")  # Enter your desired text
            print("Entered text into the post editor.")
        except Exception as e:
            print(f"Failed to locate or interact with the post editor: {e}")
            return

        # Optional: Wait for the text to appear or be processed by the editor
        time.sleep(2)

        # Step 7: Click the "Post" Button to Submit the Blog Post
        try:
            # Assuming there's another "Post" button to confirm submission
            submit_post_button = wait.until(EC.element_to_be_clickable((By.XPATH, '//button[contains(text(), "Post")]')))
            submit_post_button.click()
            print("Clicked the 'Post' button to submit the blog post.")
        except Exception as e:
            print(f"Failed to locate or click the submit 'Post' button: {e}")
            return

        # Step 8: Wait for Confirmation that the Post Was Submitted
        try:
            # Adjust the XPath to match a success message or element that appears after posting
            success_message = wait.until(EC.presence_of_element_located((By.XPATH, '//div[contains(text(), "Post successful")]')))
            print("Post submitted successfully!")
        except:
            print("Post submission may have failed or confirmation element not found.")

        # Optional: Save updated cookies and local storage after posting
        save_cookies_and_storage(driver, COOKIES_FILE, STORAGE_FILE)

        # Wait before closing to ensure all actions are completed
        time.sleep(5)

    except Exception as e:
        print(f"An unexpected error occurred during automation: {e}")

    finally:
        # Close the browser
        driver.quit()
        print("Browser closed.")

if __name__ == "__main__":
    automate_blog_post()
