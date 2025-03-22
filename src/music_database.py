import sqlite3
import os

DATABASE_FILEPATH = os.path.join(os.path.dirname(os.path.abspath(__file__)), "../assets/all_music.sqlite")

def main():
    add_song_to_db("D:/penis.flac", "penis", "the balls", "cock chronicles", 69420, "spotifyuri")
    
def add_song_to_db(filepath, title, artist, album, length, uri):
    conn = sqlite3.connect(DATABASE_FILEPATH)
    cursor = conn.cursor()

    cursor.execute('''
    CREATE TABLE IF NOT EXISTS all_music (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        filepath TEXT NOT NULL UNIQUE,
        title TEXT,
        artist TEXT,
        album TEXT,
        length INTEGER,
        uri TEXT
    )
    ''')

    try:
        song_data = (filepath, title, artist, album, length, uri)
        cursor.execute("INSERT INTO all_music (filepath, title, artist, album, length, uri) VALUES (?, ?, ?, ?, ?, ?)", song_data)
        conn.commit()
    except sqlite3.IntegrityError:
        print("Error: a song with this filepath already exists in the database.")
    finally:
        conn.close()


if __name__ == "__main__":
    add_song_to_db("D:/penis.flac", "penis", "the balls", "cock chronicles", 69420, "spotifyuri")
