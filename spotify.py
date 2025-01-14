import spotipy
from spotipy.oauth2 import SpotifyOAuth
import json
import os
from dotenv import load_dotenv

load_dotenv()

CLIENT_ID = os.getenv("client_id")
CLIENT_SECRET = os.getenv("client_secret")
REDIRECT_URI = os.getenv("redirect_uri")
SPOTIFY_SCOPE = "user-library-read"
spotipy_client = spotipy.Spotify(auth_manager=SpotifyOAuth(scope=SPOTIFY_SCOPE, client_id=CLIENT_ID,
                                                           client_secret=CLIENT_SECRET, redirect_uri=REDIRECT_URI))
USER_ID = spotipy_client.current_user()["id"]


def dump_json(contents, filepath):
    with open(filepath, "w", encoding="utf-8") as file:
        json.dump(contents, file)


def get_all_playlists(json_filepath=None):
    playlists_info = spotipy_client.user_playlists(USER_ID, limit=1)
    num_playlists = playlists_info["total"]

    all_playlists = []
    offset = 0

    while offset < num_playlists:
        new_playlists = spotipy_client.user_playlists(USER_ID, limit=50, offset=offset)
        all_playlists.extend(new_playlists["items"])
        offset += 50

    if json_filepath is not None:
        dump_json(all_playlists, json_filepath)

    return all_playlists


def main():
    playlists = get_all_playlists()
    for playlist in playlists:
        if playlist["name"] == "sldl":
            # TODO: this only gets the first 100 tracks
            tracks = spotipy_client.playlist_tracks(playlist_id=playlist["id"])
            print(len(tracks["items"]))
            dump_json(tracks, "tracks.json")

if __name__ == "__main__":
    main()
