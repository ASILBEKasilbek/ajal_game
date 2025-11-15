# from moviepy.video.io.VideoFileClip import VideoFileClip

# clip = VideoFileClip("ajal_game_gif.mov")
# clip.write_videofile("ajal_game_gif.mp4", codec="libx264")
# clip.close()


import sqlite3

# Bazaga ulanamiz
conn = sqlite3.connect("ajal_oyini.db")
cursor = conn.cursor()

# Barcha table nomlarini olish
cursor.execute("SELECT name FROM sqlite_master WHERE type='table';")
tables = cursor.fetchall()

print("📋 Jadval nomlari:")
for table in tables:
    print("-", table[0])

# Har bir jadvaldagi ustunlarni ko‘rish
print("\n📊 Jadval ustunlari:")
for table in tables:
    table_name = table[0]
    cursor.execute(f"PRAGMA table_info({table_name});")
    columns = cursor.fetchall()
    print(f"\n{table_name}:")
    for col in columns:
        print("  -", col[1])
        

conn.close()


"""

📋 Jadval nomlari:
- users
- groups
- games
- players
- admins
- rounds
- diamond_purchases
- round_players
- votes
- hang_votes

📊 Jadval ustunlari:

users:
  - id
  - telegram_id
  - username
  - hero_name
  - language
  - diamonds
  - full_name
  - created_at
  - points

groups:
  - id
  - group_id
  - group_name
  - language
  - status
  - added_by_admin
  - created_at
  - username
  - invite_link

games:
  - id
  - group_id
  - creator_user_id
  - status
  - round_number
  - start_time
  - end_time
  - join_message_id
  - najiro_player_id
  - savior_player_id
  - savior_used
  - mutanabiy_player_id

players:
  - id
  - game_id
  - user_id
  - hero_name
  - is_alive
  - diamond_saves_used
  - skip_next_voting
  - joined_at

admins:
  - id
  - telegram_id
  - username
  - added_by
  - added_at
  - is_active

rounds:
  - id
  - game_id
  - round_number
  - cards_in_play
  - status
  - start_time
  - end_time
  - suspect_player_id
  - suspect_hanged
  - suspect_used_diamond

diamond_purchases:
  - id
  - user_id
  - diamond_package
  - amount
  - screenshot_file_id
  - status
  - created_at
  - approved_by
  - approved_at

round_players:
  - id
  - round_id
  - player_id
  - card_name
  - guessed_card
  - is_correct
  - answered_at

votes:
  - id
  - round_id
  - voter_player_id
  - suspected_player_id
  - voted_at

hang_votes:
  - id
  - round_id
  - voter_player_id
  - vote
  - voted_at


"""