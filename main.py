from service.scrape_post import scrape_post
from service.scrape_comments import scrape_comments
from service.screenshot import save_screenshots_for_posts
from service.audio import generate_audio_for_post
from service.video import create_final_video
from service.instagram import upload_post
from pprint import pprint
import os
import random
import json


def main():
    history_file = "generated_videos.json"
    generated_history = []
    if os.path.exists(history_file):
        try:
            with open(history_file, "r") as f:
                generated_history = json.load(f)
        except json.JSONDecodeError:
            pass

    print("Fetching top posts...")
    limit = 3
    subreddit = "shittyaskreddit"
    response = scrape_post(subreddit=subreddit, limit=limit, time_filter="month")
    if not response:
        print("Failed to fetch posts.")
        return

    print(f"Fetched {len(response)} posts.")

    for i, post in enumerate(response):
        print(f"\n{'='*40}")
        print(f"Processing Post {i + 1}/{len(response)}: {post['title'][:50]}...")

        print(f"\nFetching comments for: {post['url']}")
        comments = scrape_comments(post["url"], limit=5)

        # 1. Take Screenshots
        print("\nStarting screenshot workflow...")
        save_screenshots_for_posts([post], [comments])

        # 2. Generate Audio (edge-tts)
        print("\nGenerating Audio TTS...")
        generate_audio_for_post(post, comments)

        # 3. Create Final Video
        print("\nStitching Final Video...")

        # Select a random background video
        bg_dir = "backgrounds"
        try:
            bg_files = [f for f in os.listdir(bg_dir) if f.endswith(".mp4")]
            bg_path = os.path.join(bg_dir, random.choice(bg_files))
            print(f"Selected background: {bg_path}")
        except Exception as e:
            print(f"Error picking background: {e}. Falling back to background.mp4")
            bg_path = "background.mp4"

        success = create_final_video(post, comments, background_vid_path=bg_path)
        if success:
            caption = f"""{post['title']} | Reddit Story\n#shorts #shortvideo #short #shortsfeed #shortsvideo #shortsviral #shortfeed #reddit #redditstories #redditstorytime #redditstory #viral #viralvideo #virealshorts #parkour #minecraft"""

            generated_history.append(
                {"post_id": post["id"], "title": post["title"], "caption": caption}
            )
            # Save incrementally
            with open(history_file, "w", encoding="utf-8") as f:
                json.dump(generated_history, f, indent=4, ensure_ascii=False)

            abs_video_path = os.path.abspath(f"content/{post['id']}/final_video.mp4")
            upload_success = upload_post(abs_video_path, caption)
            if upload_success:
                print("upload complete")
            else:
                print("failed to upload")

    print("\n🎉 Full Pipeline Completed for all posts!")


if __name__ == "__main__":
    main()
