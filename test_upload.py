from service.instagram import upload_post
print("testing upload...")
success = upload_post("content/1rneqze/final_video.mp4", "test caption")
print("success:", success)
