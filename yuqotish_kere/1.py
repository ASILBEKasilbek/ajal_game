from moviepy.video.io.VideoFileClip import VideoFileClip

clip = VideoFileClip("card_choose.mov")
clip.write_videofile("card_choose.mp4", codec="libx264")
clip.close()
