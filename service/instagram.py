import os
import time
import pickle
from dotenv import load_dotenv
from selenium import webdriver
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from selenium.webdriver.chrome.service import Service
from webdriver_manager.chrome import ChromeDriverManager
from selenium.common.exceptions import TimeoutException
from selenium.webdriver.common.keys import Keys
from selenium.webdriver.common.action_chains import ActionChains

load_dotenv()
USERNAME = os.getenv("USERNAME")
PASSWORD = os.getenv("PASSWORD")


def upload_post(video_path: str, caption: str):
    # Ensure video has absolute path so file input works
    abs_video_path = os.path.abspath(video_path)
    print(f"[Instagram] Uploading reel {abs_video_path}")

    options = webdriver.ChromeOptions()
    options.add_argument("--disable-notifications")
    options.add_argument("--no-sandbox")
    # Setting an English locale helps avoid varying element text
    options.add_argument("--lang=en")
    options.add_argument("window-size=1200,800")

    # We leave headless OFF here so the user can complete challenges if needed.
    # options.add_argument("--headless")

    driver = webdriver.Chrome(
        service=Service(ChromeDriverManager().install()), options=options
    )
    wait = WebDriverWait(driver, 15)

    try:
        driver.get("https://www.instagram.com/")
        time.sleep(3)

        cookies_file = "instagram_cookies.pkl"

        # 1. Try Loading Cookies
        if os.path.exists(cookies_file):
            print("[Instagram] Loading saved cookies...")
            with open(cookies_file, "rb") as f:
                cookies = pickle.load(f)
                for cookie in cookies:
                    driver.add_cookie(cookie)
            driver.refresh()
            time.sleep(3)

        # 2. Check if Login is Required
        try:
            # If the username input field is present, we are not logged in
            # The DOM extraction showed that Instagram uses name="email" for the username box and "pass" for password
            username_input = wait.until(
                EC.presence_of_element_located((By.NAME, "email"))
            )
            print("[Instagram] Not logged in, performing manual login...")

            # Instagram's React inputs sometimes ignore basic send_keys. We click first to focus.
            username_input.click()
            time.sleep(0.5)
            username_input.send_keys(USERNAME)
            time.sleep(0.5)

            password_input = driver.find_element(By.NAME, "pass")
            password_input.click()
            time.sleep(0.5)
            password_input.send_keys(PASSWORD)
            time.sleep(0.5)

            # Using ActionChains to press ENTER instead of finding the submit button
            password_input.send_keys(Keys.ENTER)

            # Wait until login completes and homepage is accessible
            # You might need to manually intervene here if Instagram asks for an email challenge!
            print(
                "[Instagram] Waiting up to 60 seconds for login to succeed or manual intervention..."
            )
            WebDriverWait(driver, 60).until(
                EC.presence_of_element_located(
                    (
                        By.XPATH,
                        "//*[@aria-label='New post']|//svg[@aria-label='New post']",
                    )
                )
            )

            print("[Instagram] Logged in successfully. Saving cookies...")
            with open(cookies_file, "wb") as f:
                pickle.dump(driver.get_cookies(), f)

        except TimeoutException:
            print("[Instagram] Already logged in via cookies or login took too long.")

        # Handle "Save your login info" popup if it appears
        try:
            save_info_btn = WebDriverWait(driver, 5).until(
                EC.element_to_be_clickable(
                    (By.XPATH, "//button[contains(text(), 'Not now')]")
                )
            )
            save_info_btn.click()
        except TimeoutException:
            pass

        # 3. Navigate to Post Creation
        print("[Instagram] Clicking New Post (+)...")
        create_btn = wait.until(
            EC.element_to_be_clickable(
                (
                    By.XPATH,
                    "//*[@aria-label='New post'] | //svg[@aria-label='New post']/ancestor::a | //svg[@aria-label='New post']/ancestor::div[@role='button']",
                )
            )
        )
        driver.execute_script(
            "arguments[0].dispatchEvent(new MouseEvent('click', {view: window, bubbles: true, cancelable: true}));",
            create_btn,
        )
        time.sleep(3)

        print("[Instagram] Selecting 'Post' from dropdown modal...")
        post_option = wait.until(
            EC.element_to_be_clickable(
                (By.XPATH, "//span[text()='Post'] | //div[text()='Post']")
            )
        )
        driver.execute_script(
            "arguments[0].dispatchEvent(new MouseEvent('click', {view: window, bubbles: true, cancelable: true}));",
            post_option,
        )
        time.sleep(3)

        # 4. Upload File
        print("[Instagram] Locating file input...")
        # The 'accept' attribute changed, so just look for any file input in the DOM
        file_input = wait.until(
            EC.presence_of_element_located((By.XPATH, "//input[@type='file']"))
        )

        # Instagram hides the file input heavily. Un-hide it before interacting.
        driver.execute_script(
            "arguments[0].style.display = 'block'; arguments[0].style.visibility = 'visible'; arguments[0].style.opacity = 1;",
            file_input,
        )
        time.sleep(1)

        file_input.send_keys(abs_video_path)
        print("[Instagram] Video file injected into input.")
        time.sleep(5)

        # 4.5 Change Aspect Ratio to Original (9:16)
        try:
            print("[Instagram] Selecting Aspect Ratio...")
            # Click the 'Select crop' button to open the dimension menu
            crop_btn = wait.until(
                EC.presence_of_element_located(
                    (
                        By.XPATH,
                        "//*[local-name()='svg' and @aria-label='Select crop']/ancestor::button | //button[.//svg[@aria-label='Select crop']] | //button[contains(@aria-label, 'crop')]",
                    )
                )
            )
            driver.execute_script(
                "arguments[0].dispatchEvent(new MouseEvent('click', {view: window, bubbles: true, cancelable: true}));",
                crop_btn,
            )
            time.sleep(2)

            # Click the 'Original' option
            original_btn = wait.until(
                EC.presence_of_element_located(
                    (
                        By.XPATH,
                        "//*[local-name()='svg' and @aria-label='Original']/ancestor::a | //*[local-name()='svg' and @aria-label='Original']/ancestor::div[@role='button'] | //span[text()='Original']/parent::div | //span[text()='Original'] | //div[text()='Original']",
                    )
                )
            )
            driver.execute_script(
                "arguments[0].dispatchEvent(new MouseEvent('click', {view: window, bubbles: true, cancelable: true}));",
                original_btn,
            )
            time.sleep(2)
        except Exception as e:
            print(
                f"[Instagram] Note: Could not change aspect ratio (it might already be original or UI changed). Skipping. {e}"
            )

        # 5. Click "Next" through the crop/edit screens
        # First Next (Crop screen)
        next_btn_1 = wait.until(
            EC.element_to_be_clickable(
                (
                    By.XPATH,
                    "//div[contains(text(), 'Next')] | //button[contains(text(), 'Next')]",
                )
            )
        )
        driver.execute_script(
            "arguments[0].dispatchEvent(new MouseEvent('click', {view: window, bubbles: true, cancelable: true}));",
            next_btn_1,
        )
        time.sleep(2)

        # Second Next (Edit screen)
        next_btn_2 = wait.until(
            EC.element_to_be_clickable(
                (
                    By.XPATH,
                    "//div[contains(text(), 'Next')] | //button[contains(text(), 'Next')]",
                )
            )
        )
        driver.execute_script(
            "arguments[0].dispatchEvent(new MouseEvent('click', {view: window, bubbles: true, cancelable: true}));",
            next_btn_2,
        )
        time.sleep(2)

        # 6. Add Caption
        print("[Instagram] Entering caption...")
        # Instagram uses a contenteditable div for the caption
        caption_area = wait.until(
            EC.presence_of_element_located(
                (By.XPATH, "//div[@aria-label='Write a caption...']")
            )
        )
        driver.execute_script(
            "arguments[0].dispatchEvent(new MouseEvent('click', {view: window, bubbles: true, cancelable: true}));",
            caption_area,
        )
        time.sleep(1)

        # Bypass ChromeDriver's BMP-only constraint (which crashes on emojis)
        # We focus the div, and inject the text using document.execCommand to emulate native pasting
        driver.execute_script(
            "arguments[0].focus(); document.execCommand('insertText', false, arguments[1]);",
            caption_area,
            caption,
        )
        time.sleep(1)

        # Dispatch a native Selenium keyboard event so React registers the content change
        caption_area.send_keys(" ")
        caption_area.send_keys(Keys.BACKSPACE)
        time.sleep(0.5)

        # Press Enter in caption area to simulate real keyboard input
        # This forces React to flush its internal state and persist the caption
        caption_area.send_keys(Keys.ENTER)
        time.sleep(1)

        # Verify caption was registered
        got = driver.execute_script(
            "return arguments[0].innerText || arguments[0].textContent || '';",
            caption_area,
        ).strip()
        print(
            f"[Instagram] Caption check: {len(got)} chars — '{got[:60]}{'...' if len(got) > 60 else ''}'"
        )
        time.sleep(2)

        # 7. Share the Reel — use ActionChains click so full browser events fire
        print("[Instagram] Clicking Share button...")
        share_btn = wait.until(
            EC.element_to_be_clickable(
                (
                    By.XPATH,
                    "//div[contains(text(), 'Share')] | //button[contains(text(), 'Share')]",
                )
            )
        )
        driver.execute_script(
            "arguments[0].scrollIntoView({block:'center'});", share_btn
        )
        time.sleep(0.5)
        ActionChains(driver).move_to_element(share_btn).click().perform()

        # Wait for the "Your reel has been shared" confirmation (can take a while)
        print("[Instagram] Waiting for share confirmation...")
        try:
            WebDriverWait(driver, 120).until(
                EC.presence_of_element_located(
                    (
                        By.XPATH,
                        "//div[contains(text(), 'Your reel has been shared')]|//span[contains(text(), 'Your reel has been shared')]|//div[contains(text(), 'Your post has been shared')]",
                    )
                )
            )
            print("[Instagram] Reel shared successfully!")
        except TimeoutException:
            print(
                "[Instagram] Note: Share confirmation text not found, but Share button was clicked. Assuming success."
            )

        # Give Instagram time to complete the background upload
        print("[Instagram] Waiting 15 seconds for network requests to finalize...")
        time.sleep(15)
        return True

    except Exception as e:
        print(f"[Instagram] Upload failed with exception: {e}")
        return False

    finally:
        # Give it an extended final grace period before severing the connection
        print(
            "[Instagram] Giving Chrome 45 seconds to finalize processing before closing..."
        )
        time.sleep(45)
        driver.quit()
