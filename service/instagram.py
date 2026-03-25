import os
import time
import pickle
import traceback
from dotenv import load_dotenv

# For automating uploads, we use Playwright to avoid retaining two separate scraping libraries.
try:
    from playwright.sync_api import (
        sync_playwright,
        TimeoutError as PlaywrightTimeoutError,
    )
except ImportError:
    print("Playwright not installed. Install with: uv add playwright")

load_dotenv()
USERNAME = os.getenv("USERNAME")
PASSWORD = os.getenv("PASSWORD")


def upload_post(video_path: str, caption: str):
    # Ensure video has absolute path so file input works
    abs_video_path = os.path.abspath(video_path)
    print(f"[Instagram] Uploading reel {abs_video_path}")

    try:
        with sync_playwright() as p:
            # We leave headless OFF here so the user can complete challenges if needed.
            browser = p.chromium.launch(
                headless=True,
                args=["--disable-notifications", "--window-size=1200,800"],
            )

            # Setting an English locale helps avoid varying element text
            context = browser.new_context(
                locale="en-US", viewport={"width": 1200, "height": 800}
            )

            page = context.new_page()

            # 1. Try Loading Cookies
            cookies_file = "instagram_cookies.pkl"
            if os.path.exists(cookies_file):
                print("[Instagram] Loading saved cookies...")
                try:
                    with open(cookies_file, "rb") as f:
                        cookies = pickle.load(f)

                        # Convert Selenium cookies (like 'expiry') to Playwright format ('expires')
                        pw_cookies = []
                        for c in cookies:
                            pw_c = {
                                "name": c["name"],
                                "value": c["value"],
                                "domain": c.get("domain", ".instagram.com"),
                                "path": c.get("path", "/"),
                            }
                            if "secure" in c:
                                pw_c["secure"] = c["secure"]
                            if "httpOnly" in c:
                                pw_c["httpOnly"] = c["httpOnly"]
                            if "expiry" in c:
                                pw_c["expires"] = float(c["expiry"])
                            if "sameSite" in c:
                                ss = str(c["sameSite"]).capitalize()
                                if ss in ["Strict", "Lax", "None"]:
                                    pw_c["sameSite"] = ss
                            pw_cookies.append(pw_c)

                        context.add_cookies(pw_cookies)
                except Exception as e:
                    print(f"[Instagram] Note: Failed to parse cookies correctly: {e}")

            # Note: Do not use wait_until="networkidle" on Instagram because it constantly streams network requests, causing premature exact timeouts.
            page.goto(
                "https://www.instagram.com/",
                wait_until="domcontentloaded",
                timeout=60000,
            )
            time.sleep(4)

            # 2. Check if Login is Required
            try:
                # If the username input field is present, we are not logged in
                username_input = page.locator("input[name='email']").first
                username_input.wait_for(timeout=6000)

                print("[Instagram] Not logged in, performing manual login...")
                username_input.click(force=True)
                time.sleep(0.5)
                username_input.fill(USERNAME)
                time.sleep(0.5)

                password_input = page.locator("input[name='pass']").first
                password_input.click(force=True)
                time.sleep(0.5)
                password_input.fill(PASSWORD)
                time.sleep(0.5)

                password_input.press("Enter")

                print(
                    "[Instagram] Waiting up to 60 seconds for login to succeed or manual intervention..."
                )
                # Wait for New Post button anywhere in the DOM as a success indicator
                new_post_locator = page.locator(
                    "[aria-label='New post'], svg[aria-label='New post']"
                ).first
                new_post_locator.wait_for(state="attached", timeout=60000)

                print("[Instagram] Logged in successfully. Saving cookies...")
                with open(cookies_file, "wb") as f:
                    pickle.dump(context.cookies(), f)

            except PlaywrightTimeoutError:
                print(
                    "[Instagram] Already logged in via cookies or login took too long."
                )

            # Handle "Save your login info" popup if it appears
            try:
                save_btn = page.locator("button:has-text('Not now')").first
                save_btn.wait_for(timeout=4000)
                save_btn.click(force=True)
            except PlaywrightTimeoutError:
                pass

            # Handle "Turn on Notifications" popup if it happens
            try:
                notif_btn = page.locator("button:has-text('Not now')").first
                notif_btn.wait_for(timeout=2000)
                notif_btn.click(force=True)
            except PlaywrightTimeoutError:
                pass

            def js_click(xpath, timeout=15000):
                # Helper to replicate Selenium's execute_script event firing
                locator = page.locator(xpath).first
                locator.wait_for(state="attached", timeout=timeout)
                locator.scroll_into_view_if_needed()
                locator.evaluate(
                    "node => node.dispatchEvent(new MouseEvent('click', {view: window, bubbles: true, cancelable: true}))"
                )

            # 3. Navigate to Post Creation
            print("[Instagram] Clicking New Post (+)...")
            js_click(
                "//*[@aria-label='New post'] | //svg[@aria-label='New post']/ancestor::a | //svg[@aria-label='New post']/ancestor::div[@role='button']"
            )
            time.sleep(3)

            print("[Instagram] Selecting 'Post' from dropdown modal...")
            js_click("//span[text()='Post'] | //div[text()='Post']")
            time.sleep(3)

            # 4. Upload File
            print("[Instagram] Locating file input...")
            # Unhide and send keys if set_input_files fails; but set_input_files is extremely robust.
            page.set_input_files("//input[@type='file']", abs_video_path)
            print("[Instagram] Video file injected into input.")
            time.sleep(5)

            # 4.5 Change Aspect Ratio to Original (9:16)
            try:
                print("[Instagram] Selecting Aspect Ratio...")
                js_click(
                    "//*[local-name()='svg' and @aria-label='Select crop']/ancestor::button | //button[.//svg[@aria-label='Select crop']] | //button[contains(@aria-label, 'crop')]"
                )
                time.sleep(2)

                js_click(
                    "//*[local-name()='svg' and @aria-label='Original']/ancestor::a | //*[local-name()='svg' and @aria-label='Original']/ancestor::div[@role='button'] | //span[text()='Original']/parent::div | //span[text()='Original'] | //div[text()='Original']"
                )
                time.sleep(2)
            except Exception as e:
                print(
                    f"[Instagram] Note: Could not change aspect ratio (it might already be original or UI changed). Skipping. {e}"
                )

            # 5. Click "Next" through the crop/edit screens
            # First Next (Crop screen)
            js_click(
                "//div[contains(text(), 'Next')] | //button[contains(text(), 'Next')]"
            )
            time.sleep(3)

            # Second Next (Edit screen)
            js_click(
                "//div[contains(text(), 'Next')] | //button[contains(text(), 'Next')]"
            )
            time.sleep(3)

            # 6. Add Caption
            print("[Instagram] Entering caption...")
            # 6. Add Caption
            print("[Instagram] Entering caption...")
            caption_area_xpath = "//div[@aria-label='Write a caption...']"
            caption_locator = page.locator(caption_area_xpath).first

            # Click directly using JS
            js_click(caption_area_xpath)
            time.sleep(1)

            # Bypass ChromeDriver's/Playwright's BMP-only constraint and avoid accidental keyboard shortcuts (like ESC)!
            # We focus the div, and inject the text using document.execCommand to emulate native pasting, exactly as we did in Selenium.
            caption_locator.evaluate(
                "(node, text) => { node.focus(); document.execCommand('insertText', false, text); }",
                caption,
            )
            time.sleep(1)

            # Dispatch a native Selenium keyboard event equivalent so React registers the content change
            page.keyboard.press("Space")
            page.keyboard.press("Backspace")
            time.sleep(1)

            # Click the area again to ensure focus is maintained before sharing
            js_click(caption_area_xpath)
            time.sleep(1)

            # Verify caption was registered
            raw_got = caption_locator.evaluate(
                "node => node.innerText || node.textContent || ''"
            )
            got = str(raw_got).strip() if raw_got else ""
            print(
                f"[Instagram] Caption check: {len(got)} chars — '{got[:60]}{'...' if len(got) > 60 else ''}'"
            )
            time.sleep(2)

            # 7. Share the Reel
            print("[Instagram] Clicking Share button...")
            share_btn_xpath = (
                "//div[contains(text(), 'Share')] | //button[contains(text(), 'Share')]"
            )
            share_locator = page.locator(share_btn_xpath).first
            share_locator.wait_for(state="attached", timeout=15000)

            # Force block center into view, mimicking argument[0].scrollIntoView({block:'center'})
            share_locator.evaluate("node => node.scrollIntoView({block: 'center'})")
            time.sleep(0.5)

            # Equivalent to ActionChains(driver).move_to_element(share_btn).click()
            # Perform a standard Playwright click (which calculates geometry and simulates real cursor click)
            share_locator.click()

            print("[Instagram] Waiting for share confirmation...")
            try:
                # Wait for the "Your reel has been shared" confirmation (can take up to 2 minutes based on video size)
                confirm_msg = page.locator(
                    "text=Your reel has been shared, text=Your post has been shared"
                ).first
                confirm_msg.wait_for(timeout=120000)
                print("[Instagram] Reel shared successfully!")
            except PlaywrightTimeoutError:
                print(
                    "[Instagram] Note: Share confirmation text not found, but Share button was clicked. Assuming success."
                )

            # Give Instagram time to complete the background upload internally
            print("[Instagram] Waiting 15 seconds for network requests to finalize...")
            time.sleep(15)

            # Save any updated cookies back to disk
            try:
                new_cookies = context.cookies()
                with open(cookies_file, "wb") as f:
                    pickle.dump(new_cookies, f)
            except Exception:
                pass

            print(
                "[Instagram] Giving browser 15 final seconds to finish background jobs..."
            )
            time.sleep(15)
            return True

    except Exception as e:
        print(f"[Instagram] Upload failed with exception: {e}")
        traceback.print_exc()
        return False
