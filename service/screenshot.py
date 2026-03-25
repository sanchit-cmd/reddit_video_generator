import os
import requests
from pathlib import Path
from typing import List
import time

# For taking screenshots, we'll use Playwright with Firefox since it evades bot detection effectively
try:
    from playwright.sync_api import sync_playwright
except ImportError:
    print("Playwright not installed. Install with: pip install playwright")


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

    Returns:
        True if successful, False otherwise
    """
    # Create folder structure: content/{post_id}/
    post_folder = Path(output_dir) / post_id
    post_folder.mkdir(parents=True, exist_ok=True)

    try:
        with sync_playwright() as p:
            # Firefox handles headless much better against bot preventions
            browser = p.firefox.launch(
                headless=True,
                # args=["--window-size=1920,1080"]
            )
            
            context = browser.new_context(
                viewport={"width": 1920, "height": 1080},
                device_scale_factor=2,  # Takes high-quality (retina) screenshots
                user_agent="Mozilla/5.0 (Windows NT 10.0; Win64; x64; rv:124.0) Gecko/20100101 Firefox/124.0"
            )
            page = context.new_page()

            page.goto(post_url, wait_until="domcontentloaded")
            time.sleep(3)

            # Hide sticky navbar and headers to prevent screenshot overlaps
            page.evaluate("""
                () => {
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
                }
            """)
            time.sleep(1)

            print(f"📸 Taking screenshot of post: {post_id}")

            # Screenshot 1: Post section
            post_screenshot_path = post_folder / "post.png"
            try:
                # Wait for the post to be visible
                page.wait_for_selector("shreddit-post", state="attached", timeout=10000)
                post_element = page.locator("shreddit-post").first
                post_element.screenshot(path=str(post_screenshot_path))
                print(f"✅ Post screenshot saved: {post_screenshot_path}")
            except Exception as e:
                print(f"❌ Error taking post screenshot: {e}")

            # Screenshot 2: Top comments section
            try:
                # Scroll down to see comments
                page.evaluate("window.scrollBy(0, 500);")
                time.sleep(2)

                # Find comment sections and take screenshots
                for i, comment in enumerate(comments):
                    comment_id = comment.get("id")
                    if not comment_id:
                        continue
                    
                    # Reddit's custom element uses thingid="t1_{comment_id}"
                    selector = f'shreddit-comment[thingid="t1_{comment_id}"]'
                    
                    try:
                        # Wait shortly for this specific comment to exist
                        page.wait_for_selector(selector, state="attached", timeout=5000)
                        comment_elem = page.locator(selector).first
                        
                        # Scroll element into view just in case
                        comment_elem.evaluate("node => node.scrollIntoView({block: 'center'});")
                        time.sleep(0.5)

                        if comment_elem.is_visible():
                            # JS ISOLATION: Hide ONLY the internal sub-comments and action rows of THIS comment
                            comment_elem.evaluate("""
                                node => {
                                    // 1. Hide any nested shreddit-comments (subcomments/replies) inside this comment
                                    node.querySelectorAll('shreddit-comment, [slot="children"]').forEach(c => {
                                        c.style.setProperty('display', 'none', 'important');
                                    });
                                    
                                    // 2. Hide action rows (upvote/reply buttons) inside this comment
                                    node.querySelectorAll('shreddit-comment-action-row').forEach(r => {
                                        r.style.setProperty('display', 'none', 'important');
                                    });
                                    
                                    // 3. Optional: Add a clean border just to frame it nicely
                                    node.style.setProperty('border', '1px solid #333', 'important');
                                    node.style.setProperty('border-radius', '8px', 'important');
                                }
                            """)
                            time.sleep(0.5)

                            comment_screenshot_path = post_folder / f"comment_{i + 1}.png"
                            comment_elem.screenshot(path=str(comment_screenshot_path))
                            print(f"✅ Comment {i + 1} (ID: {comment_id}) screenshot saved: {comment_screenshot_path}")

                            # JS RESTORATION: Undo the hiding so we can scroll correctly to the next one
                            comment_elem.evaluate("""
                                node => {
                                    node.querySelectorAll('*').forEach(el => el.style.removeProperty('display'));
                                    node.style.removeProperty('border');
                                    node.style.removeProperty('border-radius');
                                }
                            """)
                            time.sleep(0.2)
                        else:
                            print(f"⚠️ Comment {i + 1} (ID: {comment_id}) is not displayed on screen.")
                    except Exception as e:
                        print(f"❌ Could not find/screenshot comment {i + 1} (ID: {comment_id}): {e}")

            except Exception as e:
                print(f"❌ Error taking comment screenshots: {e}")

            browser.close()
            print(f"\n✨ All screenshots saved to: {post_folder}")
            return True

    except Exception as e:
        print(f"❌ Error during screenshot process: {e}")
        return False


def save_screenshots_for_posts(
    posts: List[dict], all_comments: List[List[dict]], output_dir: str = "content"
) -> None:
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
