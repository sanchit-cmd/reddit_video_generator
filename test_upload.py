import os
import sys

# Ensure the parent directory is in the path
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from service.instagram import upload_post

if __name__ == "__main__":
    print("testing upload...")
    
    # Path to sample video
    # Note: Use a valid absolute path to a generated video
    test_video_path = os.path.abspath("backgrounds/background_1.mp4")
    
    if not os.path.exists(test_video_path):
         print(f"Error: Could not find test video at {test_video_path}")
         print("Please run the generator first or place a sample video there.")
         sys.exit(1)

    caption = "This is a test reel! 🚀🔥 #shorts #reddit"
    
    success = upload_post(test_video_path, caption)
    print(f"\nsuccess: {success}")
