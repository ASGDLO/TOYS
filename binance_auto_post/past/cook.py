import json
from selenium import webdriver
from selenium.webdriver.chrome.service import Service as ChromeService
from selenium.webdriver.chrome.options import Options
import time

# Path to your ChromeDriver
CHROME_DRIVER_PATH = '/usr/local/bin/chromedriver'  # Update as needed

# Configure ChromeOptions to use a temporary profile for extraction
chrome_options = Options()
chrome_options.add_argument('--user-data-dir=/tmp/temp_profile')  # Temporary profile
# Optional: Run Chrome in headless mode
# chrome_options.add_argument('--headless')

# Initialize the Chrome WebDriver
service = ChromeService(executable_path=CHROME_DRIVER_PATH)
driver = webdriver.Chrome(service=service, options=chrome_options)

try:
    # Open Binance and perform manual login
    driver.get("https://www.binance.com/en/login")
    print("Please log in manually within the opened browser window.")
    
    # Wait sufficient time for manual login
    time.sleep(60)  # Adjust as needed based on your login speed
    
    # Save cookies to a file
    cookies = driver.get_cookies()
    with open('cookies.json', 'w') as file:
        json.dump(cookies, file)
    print("Cookies have been saved to 'cookies.json'.")

    # Save local storage to a file
    local_storage = driver.execute_script("return window.localStorage;")
    with open('local_storage.json', 'w') as file:
        json.dump(local_storage, file)
    print("Local storage has been saved to 'local_storage.json'.")

except Exception as e:
    print(f"An error occurred during extraction: {e}")

finally:
    # Close the browser
    driver.quit()
    print("Browser closed after extraction.")
