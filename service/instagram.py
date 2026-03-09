import os
import shutil
from instabot import Bot


def upload_post(video_path: str, caption: str):
    # instabot is notorious for storing a config folder that gets corrupted
    # it's best to delete it before logging in to ensure a fresh session
    config_dir = "config"
    if os.path.exists(config_dir):
        try:
            shutil.rmtree(config_dir)
        except Exception as e:
            print(f"[Instagram] Warning: could not empty config dir: {e}")

    try:
        bot = Bot()
        bot.login(username="red.dit.shorts", password="elonMusk@2005")

        # Ensure the path is absolute or correct relative to execution dir
        print(f"[Instagram] Uploading video {video_path}...")
        bot.upload_video(video_path, caption=caption)

        bot.logout()
        print("[Instagram] Upload successful!")
        return True
    except Exception as e:
        print(f"[Instagram] Upload failed with exception: {e}")
        return False
