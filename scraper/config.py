from selenium import webdriver
from selenium.webdriver.chrome.service import Service
from webdriver_manager.chrome import ChromeDriverManager
from selenium.webdriver.chrome.options import Options

def get_driver():
    """
    Instantiates and returns a configured Selenium WebDriver instance with Chrome options.
    
    Returns:
        webdriver.Chrome: A Selenium WebDriver instance configured with necessary options.
    """
    chrome_options = Options()
    chrome_options.binary_location = '/usr/bin/google-chrome'
    chrome_options.add_experimental_option("detach", True)
    driver = webdriver.Chrome(service = Service(ChromeDriverManager().install()), options = chrome_options)
    return driver


def quit_driver(driver):
    """
    Quits the provided WebDriver instance.

    This function closes all browser windows and ends the WebDriver session.

    Args:
        driver (webdriver): The WebDriver instance that is controlling the browser.

    Returns:
        None
    """
    try:
        if driver is not None:
            driver.quit()
            print("Driver successfully quit.")
        else:
            print("No active driver to quit.")
    except Exception as e:
        print(f"Error quitting the driver: {e}")