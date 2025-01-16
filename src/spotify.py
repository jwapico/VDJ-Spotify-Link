import spotipy
from spotipy.oauth2 import SpotifyOAuth
import json
import os
from dotenv import load_dotenv
import xml.etree.ElementTree as ET
from pathlib import Path
from xml.dom import minidom

load_dotenv()

CLIENT_ID = os.getenv("client_id")
CLIENT_SECRET = os.getenv("client_secret")
REDIRECT_URI = os.getenv("redirect_uri")
SPOTIFY_SCOPE = "user-library-read"
spotipy_client = spotipy.Spotify(auth_manager=SpotifyOAuth(scope=SPOTIFY_SCOPE, client_id=CLIENT_ID, client_secret=CLIENT_SECRET, redirect_uri=REDIRECT_URI))
USER_ID = spotipy_client.current_user()["id"]

def main():
    playlists = get_all_playlists()
    for playlist in playlists:
        if playlist["name"] == "test":
            get_all_playlist_tracks(playlist["id"])
            create_vdjfolder_from_playlist(playlist_id=playlist["id"], vdjfolder_filepath="output/test.xml")

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

def get_all_playlist_tracks(playlist_id, json_filepath=None):
    all_tracks = []
    offset = 0

    while True:
        response = spotipy_client.playlist_items(playlist_id=playlist_id, offset=offset)
        all_tracks.extend(response["items"])
        offset += 100

        if len(response["items"]) < 100:
            break
        
    if json_filepath is not None:
        dump_json(all_tracks, json_filepath)

def dump_json(contents, json_filepath):
    with open(json_filepath, "w", encoding="utf-8") as file:
        json.dump(contents, file)

# creates a .vdjfolder file from a playlist_id
def create_vdjfolder_from_playlist(playlist_id, vdjfolder_filepath):
    # create the root and song entries
    root = ET.Element("VirtualFolder", noDuplicates="no")
    ET.SubElement(root, "song1", path="D:/path1.mp3", title="hello title1", artist="hello artist1")
    ET.SubElement(root, "song2", path="D:/path2.mp3", title="hello title2", artist="hello artist2")

    # create the output_dir if it doesnt already exist
    output_dir = os.path.dirname(vdjfolder_filepath)
    Path(output_dir).mkdir(parents=True, exist_ok=True)
    
    # reparse the string with minidom to get formatting
    rough_string = ET.tostring(root, encoding="utf-8")
    reparsed = minidom.parseString(rough_string)
    pretty_xml = reparsed.toprettyxml(indent="    ")

    # write the header and formatted xml
    with open(vdjfolder_filepath, "w", encoding="utf-8") as file:
        file.write('<?xml version="1.0" encoding="UTF-8"?>\n')
        file.write(pretty_xml.split('\n', 1)[1])


if __name__ == "__main__":
    main()
