import requests
import re
from pprint import pprint
from typing import List, Dict


def scrape_comments(
    post_url: str, limit: int = 3, max_length: int = 300, min_length=30
) -> List[Dict]:
    """
    Scrape top comments from a Reddit post using Reddit's JSON API.

    Args:
        post_url: Full URL of the Reddit post (e.g., https://reddit.com/r/AskReddit/comments/1rnck41/...)
                  or just the post ID (e.g., 1rnck41)
        limit: Number of top comments to scrape (default: 3)
        max_words: Maximum word count for a comment (default: 100)

    Returns:
        List of dictionaries containing comment data (author, score, text)
    """
    # Convert post ID to full URL if necessary
    if not post_url.startswith("http"):
        post_url = f"https://reddit.com/r/AskReddit/comments/{post_url}/"

    # Append .json to get JSON response
    json_url = post_url.rstrip("/") + "/.json"

    headers = {
        "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36"
    }

    try:
        response = requests.get(json_url, headers=headers, timeout=10)
        response.raise_for_status()
        data = response.json()
    except requests.RequestException as e:
        print(f"Error fetching the post: {e}")
        return []
    except ValueError as e:
        print(f"Error parsing JSON: {e}")
        return []

    comments = []

    try:
        # Reddit returns comments data in the second element of the response array
        if isinstance(data, list) and len(data) > 1:
            comments_data = data[1].get("data", {}).get("children", [])
        else:
            print("Unexpected response format")
            return []

        comment_count = 0
        for comment_item in comments_data:
            if comment_count >= limit:
                break

            comment = comment_item.get("data", {})

            # Skip if it's a "more comments" placeholder
            if comment_item.get("kind") == "more":
                continue

            # Only get comments with actual text
            if not comment.get("body") or comment.get("body") == "[deleted]":
                continue

            comment_text = comment.get("body", "").strip()
            
            # Skip comments that are too short or too long
            if len(comment_text) < min_length or len(comment_text) > max_length:
                continue

            # Skip comments with links (http, https, www)
            if re.search(r"https?://\S+|www\.\S+", comment_text):
                print(f"Skipping comment {comment.get('id')} - contains link")
                continue

            # Skip comments with Reddit video/GIF/image syntax ![gif](...) or ![img](...)
            if "![" in comment_text and "](" in comment_text:
                print(f"Skipping comment {comment.get('id')} - contains embed/GIF")
                continue

            comment_data = {
                "id": comment.get("id", ""),
                "author": comment.get("author", "Unknown"),
                "score": comment.get("score", 0),
                "text": comment_text,
                "created_at": comment.get("created_utc", 0),
            }

            comments.append(comment_data)
            comment_count += 1

    except Exception as e:
        print(f"Error parsing comments: {e}")
        return []

    return comments


# Example usage
if __name__ == "__main__":
    # Example post URL from AskReddit
    post_url = "https://reddit.com/r/AskReddit/comments/1rnck41/bernie_sanders_proposed_a_bill_to_tax/"

    comments = scrape_comments(post_url=post_url, limit=3, max_words=100)

    print(f"Found {len(comments)} top comments (max 100 words):\n")
    pprint(comments)
