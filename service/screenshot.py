import os
import requests
from pathlib import Path
from typing import List
import time

# For taking screenshots, we'll use selenium with a headless browser
try:
    from selenium import webdriver
    from selenium.webdriver.common.by import By
    from selenium.webdriver.support.ui import WebDriverWait
    from selenium.webdriver.support import expected_conditions as EC
    from selenium.webdriver.chrome.options import Options
except ImportError:
    print("Selenium not installed. Install with: pip install selenium")


def screenshot_post_and_comments(
    post_url: str, post_id: str, comments: List[dict], output_dir: str = "content"
) -> bool:
    """
    Take screenshots of a Reddit post and its top comments.

    Args:
        post_url: Full URL of the Reddit post
        post_id: The ID of the post (used for folder naming)
        comments: List of comment dictionaries (from scrape_comments) to sync with
        output_dir: Base directory to store screenshots (default: 'content')
        output_dir: Base directory to store screenshots (default: 'content')

    Returns:
        True if successful, False otherwise
    """
    # Create folder structure: content/{post_id}/
    post_folder = Path(output_dir) / post_id
    post_folder.mkdir(parents=True, exist_ok=True)

    # Setup Chrome options for headless browsing
    chrome_options = Options()
    # chrome_options.add_argument("--headless")
    chrome_options.add_argument("--no-sandbox")
    chrome_options.add_argument("--disable-dev-shm-usage")
    chrome_options.add_argument("--window-size=1920,1080")
    chrome_options.add_argument("--disable-gpu")

    try:
        # Initialize webdriver
        driver = webdriver.Chrome(options=chrome_options)
        driver.get(post_url)

        # Wait for page to load
        time.sleep(3)

        # Hide sticky navbar and headers to prevent screenshot overlaps
        driver.execute_script("""
            const style = document.createElement('style');
            style.innerHTML = `
                shreddit-header,
                reddit-header-large,
                reddit-header-small,
                #header {
                    display: none !important;
                }
            `;
            document.head.appendChild(style);
        """)
        time.sleep(1)

        print(f"📸 Taking screenshot of post: {post_id}")

        # Screenshot 1: Post section
        post_screenshot_path = post_folder / "post.png"
        try:
            # Wait for the post to be visible
            WebDriverWait(driver, 10).until(
                EC.presence_of_element_located((By.TAG_NAME, "shreddit-post"))
            )

            # Find and screenshot the post element
            post_element = driver.find_element(By.TAG_NAME, "shreddit-post")
            post_element.screenshot(str(post_screenshot_path))
            print(f"✅ Post screenshot saved: {post_screenshot_path}")
        except Exception as e:
            print(f"❌ Error taking post screenshot: {e}")

        # Screenshot 2: Top comments section
        try:
            # Scroll down to see comments
            driver.execute_script("window.scrollBy(0, 500);")
            time.sleep(2)

            time.sleep(2)

            # Find comment sections and take screenshots
            # Instead of iterating over whatever is visually first, we loop over
            # the exact comments we generated audio for, and find them by id.
            for i, comment in enumerate(comments):
                comment_id = comment.get("id")
                if not comment_id:
                    continue
                
                # Reddit's custom element uses thingid="t1_{comment_id}"
                selector = f'shreddit-comment[thingid="t1_{comment_id}"]'
                
                try:
                    # Wait shortly for this specific comment to exist
                    EC.presence_of_element_located((By.CSS_SELECTOR, selector))(driver)
                    comment_elem = driver.find_element(By.CSS_SELECTOR, selector)
                    
                    # Scroll element into view just in case
                    driver.execute_script("arguments[0].scrollIntoView({block: 'center'});", comment_elem)
                    time.sleep(0.5)

                    if comment_elem.is_displayed():
                        # JS ISOLATION: Hide ONLY the internal sub-comments and action rows of THIS comment
                        driver.execute_script("""
                            const target = arguments[0];
                            
                            // 1. Hide any nested shreddit-comments (subcomments/replies) inside this comment
                            target.querySelectorAll('shreddit-comment, [slot="children"]').forEach(c => {
                                c.style.setProperty('display', 'none', 'important');
                            });
                            
                            // 2. Hide action rows (upvote/reply buttons) inside this comment
                            target.querySelectorAll('shreddit-comment-action-row').forEach(r => {
                                r.style.setProperty('display', 'none', 'important');
                            });
                            
                            // 3. Optional: Add a clean border just to frame it nicely
                            target.style.setProperty('border', '1px solid #333', 'important');
                            target.style.setProperty('border-radius', '8px', 'important');
                        """, comment_elem)
                        time.sleep(0.5) # Allow render flush

                        comment_screenshot_path = post_folder / f"comment_{i + 1}.png"
                        comment_elem.screenshot(str(comment_screenshot_path))
                        print(f"✅ Comment {i + 1} (ID: {comment_id}) screenshot saved: {comment_screenshot_path}")

                        # JS RESTORATION: Undo the hiding so we can scroll correctly to the next one
                        driver.execute_script("""
                            const target = arguments[0];
                            target.querySelectorAll('*').forEach(el => el.style.removeProperty('display'));
                            target.style.removeProperty('border');
                            target.style.removeProperty('border-radius');
                        """, comment_elem)
                        time.sleep(0.2)
                    else:
                        print(f"⚠️ Comment {i + 1} (ID: {comment_id}) is not displayed on screen.")
                except Exception as e:
                    print(f"❌ Could not find/screenshot comment {i + 1} (ID: {comment_id}): {e}")

        except Exception as e:
            print(f"❌ Error taking comment screenshots: {e}")

        driver.quit()
        print(f"\n✨ All screenshots saved to: {post_folder}")
        return True

    except Exception as e:
        print(f"❌ Error during screenshot process: {e}")
        return False


def save_screenshots_for_posts(posts: List[dict], all_comments: List[List[dict]], output_dir: str = "content") -> None:
    """
    Save screenshots for a list of posts and their associated comments.

    Args:
        posts: List of post dictionaries
        all_comments: List of lists containing comments for each post
        output_dir: Base directory to store screenshots
    """
    for i, post in enumerate(posts):
        post_id = post.get("id")
        post_url = post.get("url")
        comments = all_comments[i] if i < len(all_comments) else []

        if not post_id or not post_url:
            print(f"⚠️ Skipping post - missing ID or URL")
            continue

        screenshot_post_and_comments(post_url, post_id, comments, output_dir)
        time.sleep(2)  # Delay between screenshots


# Example usage
if __name__ == "__main__":
    # Example: Screenshot a single post
    post_url = "https://reddit.com/r/AskReddit/comments/1rnck41/bernie_sanders_proposed_a_bill_to_tax/"
    post_id = "1rnck41"
    comments = [{"id": "o95pueg", "text": "Test"}]

    screenshot_post_and_comments(post_url, post_id, comments)
