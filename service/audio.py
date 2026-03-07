import subprocess
from pathlib import Path


def generate_audio_for_post(post, comments, output_dir="content"):
    """
    Generate MP3 files for the post title and the top comments using edge-tts.
    """
    post_id = post.get("id")
    post_folder = Path(output_dir) / post_id
    post_folder.mkdir(parents=True, exist_ok=True)

    # Edge-TTS voice choice (very natural and realistic male voice)
    voice = "en-US-ChristopherNeural"

    print(f"🎙️ Generating hyper-realistic audio for post: {post_id}")

    # Generate audio for the main post
    post_title = post.get("title", "")
    if post_title:
        post_audio_path = post_folder / "post.mp3"
        try:
            # We use the CLI edge-tts instead of the async python library for simpler sync execution
            subprocess.run([
                "edge-tts",
                "--voice", voice,
                "--text", post_title,
                "--write-media", str(post_audio_path)
            ], check=True)
            print(f"✅ Post audio saved: {post_audio_path}")
        except Exception as e:
            print(f"❌ Error generating audio for post: {e}")

    # Generate audio for the comments
    for i, comment in enumerate(comments):
        text = comment.get("text", "")
        if text:
            comment_audio_path = post_folder / f"comment_{i + 1}.mp3"
            try:
                subprocess.run([
                    "edge-tts",
                    "--voice", voice,
                    "--text", text,
                    "--write-media", str(comment_audio_path)
                ], check=True)
                print(f"✅ Comment {i + 1} audio saved: {comment_audio_path}")
            except Exception as e:
                print(f"❌ Error generating audio for comment {i + 1}: {e}")

    return True


# Example usage
if __name__ == "__main__":
    test_post = {
        "id": "1rnck41",
        "title": "This is a test title for a Reddit post."
    }
    test_comments = [
        {"text": "This is the first comment."},
        {"text": "And this is the second comment."}
    ]
    generate_audio_for_post(test_post, test_comments)
