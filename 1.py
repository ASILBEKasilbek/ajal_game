from moviepy.video.io.VideoFileClip import VideoFileClip

clip = VideoFileClip("kun.mov")
clip.write_videofile("kun.mp4", codec="libx264")
clip.close()
