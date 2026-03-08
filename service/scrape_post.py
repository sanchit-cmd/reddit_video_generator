import requests
import json
from pprint import pprint
from typing import List, Dict


def scrape_post(
    subreddit: str = "AskReddit",
    limit: int = 5,
    time_filter: str = "day",
    max_title_length: int = 150,
) -> List[Dict]:
    """
    Scrape top posts from a given subreddit using Reddit's JSON API.

    Args:
        subreddit: Subreddit name (without r/)
        limit: Number of posts to scrape (default: 5)
        time_filter: Time filter for top posts - 'day', 'week', 'month', 'year', 'all'
        max_title_length: Maximum length of the title (default: 150)

    Returns:
        List of dictionaries containing post data (title, author, score, url, comments)
    """
    # Fetch a larger batch to account for filtered out NSFW posts
    fetch_limit = max(limit * 3, 25)
    link = f"https://www.reddit.com/r/{subreddit}/top/.json?t={time_filter}&limit={fetch_limit}"

    headers = {
        "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36"
    }

    try:
        response = requests.get(link, headers=headers, timeout=10)
        response.raise_for_status()
        data = response.json()
    except requests.RequestException as e:
        print(f"Error fetching the page: {e}")
        return []
    except ValueError as e:
        print(f"Error parsing JSON: {e}")
        return []

    posts = []

    try:
        # Extract posts from the JSON response
        posts_data = data.get("data", {}).get("children", [])

        for post_item in posts_data:
            if len(posts) >= limit:
                break

            post = post_item.get("data", {})

            # Skip NSFW / 18+ content
            if post.get("over_18"):
                continue

            # Skip posts with excessively long titles
            title = post.get("title", "")
            if len(title) > max_title_length:
                continue

            post_data = {
                "id": post.get("id", ""),
                "title": post.get("title", ""),
                "author": post.get("author", "Unknown"),
                "score": post.get("score", 0),
                "url": f"https://reddit.com{post.get('permalink', '')}",
                "comments": post.get("num_comments", 0),
                "content": post.get("selftext", "")[:500],  # First 500 chars of content
            }

            posts.append(post_data)

    except Exception as e:
        print(f"Error parsing posts: {e}")
        return []

    return posts


# Example usage
if __name__ == "__main__":
    # Scrape top 5 posts from AskReddit
    posts = scrape_post(subreddit="AskReddit", limit=5, time_filter="day")

    print(f"Found {len(posts)} posts:\n")
    pprint(posts)
