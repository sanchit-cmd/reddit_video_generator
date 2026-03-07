import os
from pathlib import Path
from moviepy import (
    VideoFileClip,
    ImageClip,
    AudioFileClip,
    CompositeVideoClip,
    CompositeAudioClip,
    concatenate_videoclips,
)


def create_final_video(post, comments, background_vid_path, output_dir="content"):
    """
    Assemble the final video using the background video, screenshots, and generated audio.
    """
    post_id = post.get("id")
    post_folder = Path(output_dir) / post_id

    # Output file
    final_output_path = post_folder / "final_video.mp4"

    print(f"🎬 Assembling video for post: {post_id}")

    try:
        # 1. Load the background video
        # We assume the background video is long enough. Later we'll trim it or loop it.
        bg_clip = VideoFileClip(str(background_vid_path)).without_audio()
        
        # We need a 9:16 aspect ratio for Instagram Reels / TikTok (1080x1920)
        # Assuming the background video is already vertical or we center-crop it.
        # For simplicity, we'll retain the target resolution if needed or just use the bg_clip resolution.
        w, h = bg_clip.size

        # 2. Build the sequences of (Image + Audio) clips
        clips_sequence = []
        total_duration = 0

        # --- Post Clip ---
        post_img_path = post_folder / "post.png"
        post_aud_path = post_folder / "post.mp3"

        if post_img_path.exists() and post_aud_path.exists():
            post_audio = AudioFileClip(str(post_aud_path))
            duration = post_audio.duration

            # Create an ImageClip, set its duration to the audio duration
            post_img = (
                ImageClip(str(post_img_path))
                .with_duration(duration)
                .with_position("center")
                # Scale the image so it fits nicely in the video (e.g., 90% width)
                .resized(width=w * 0.9)
            )
            # Attach audio to the image clip
            post_img = post_img.with_audio(post_audio)

            clips_sequence.append(post_img)
            total_duration += duration
        else:
            print("❌ Post screenshot or audio is missing. Skipping post clip.")

        # --- Comments Clips ---
        for i in range(len(comments)):
            comment_img_path = post_folder / f"comment_{i + 1}.png"
            comment_aud_path = post_folder / f"comment_{i + 1}.mp3"

            if comment_img_path.exists() and comment_aud_path.exists():
                comment_audio = AudioFileClip(str(comment_aud_path))
                duration = comment_audio.duration

                comment_img = (
                    ImageClip(str(comment_img_path))
                    .with_duration(duration)
                    .with_position("center")
                    # Same scaling as above
                    .resized(width=w * 0.9)
                )
                comment_img = comment_img.with_audio(comment_audio)

                clips_sequence.append(comment_img)
                total_duration += duration
            else:
                print(f"⚠️ Comment {i + 1} screenshot or audio missing. Skipping.")

        # If no clips were generated, return
        if not clips_sequence:
            print("❌ No valid clips to assemble.")
            return False

        # 3. Concatenate the image sequences sequentially
        # This creates a single clip consisting of the screenshots playing one after another
        foreground_clip = concatenate_videoclips(clips_sequence, method="compose").with_position("center")

        # 4. Trim the background video to the total duration of the spoken content
        # If the background clip is shorter than total_duration, loop it
        if bg_clip.duration < total_duration:
             from moviepy.video.fx import Loop
             bg_clip = bg_clip.with_effects([Loop(duration=total_duration)])
        
        bg_clip = bg_clip.subclipped(0, total_duration)

        # 5. Composite the foreground over the background
        final_video = CompositeVideoClip([bg_clip, foreground_clip])

        # 6. Render the final output
        final_video.write_videofile(
            str(final_output_path),
            fps=30,
            codec="libx264",
            audio_codec="aac",
            preset="ultrafast",
            threads=4
        )

        print(f"✨ Final video successfully generated: {final_output_path}")
        
        # Close clips to free memory
        bg_clip.close()
        final_video.close()
        return True

    except Exception as e:
        print(f"❌ Error during video assembly: {e}")
        return False
