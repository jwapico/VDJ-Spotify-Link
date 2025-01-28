import spotipy
from spotipy.oauth2 import SpotifyOAuth
import json
import os
from dotenv import load_dotenv
import xml.etree.ElementTree as ET
from pathlib import Path
from xml.dom import minidom
from tinytag import TinyTag

load_dotenv()

CLIENT_ID = os.getenv("client_id")
CLIENT_SECRET = os.getenv("client_secret")
REDIRECT_URI = os.getenv("redirect_uri")
SPOTIFY_SCOPE = "user-library-read playlist-modify-public"
spotipy_client = spotipy.Spotify(auth_manager=SpotifyOAuth(scope=SPOTIFY_SCOPE, client_id=CLIENT_ID, client_secret=CLIENT_SECRET, redirect_uri=REDIRECT_URI))
USER_ID = spotipy_client.current_user()["id"]
MUSIC_DIR = "D:\DJ\Music\Spotify Liked"

def main():
    create_spotify_playlist_from_music_dir("D:\DJ\Music\DJ Music\NeoSoul")

def create_spotify_playlist_from_music_dir(music_dir):
    pass

def create_spotify_playlist_from_vdjfolder(vdjfolder_filepath, playlist_name):
    tree = ET.parse(vdjfolder_filepath)

    track_ids = []
    for child in tree.getroot():
        if "title" in child.attrib and "artist" in child.attrib:
            title = child.attrib["title"]
            artist = child.attrib["artist"]
            track_id = spotipy_client.search(q=f"artist: {artist} track: {title}", type="track")
            track_ids.append(track_id["tracks"]["items"][0]["id"])
    
    track_uris = ["spotify:track:" + track_id for track_id in track_ids]
    spotipy_client.user_playlist_create(USER_ID, playlist_name)
    playlist_id = get_playlist_id(playlist_name)
    spotipy_client.user_playlist_add_tracks(USER_ID, playlist_id, track_uris)

def get_playlist_id(playlist_name):
    for playlist in get_all_playlists():
        if playlist["name"] == playlist_name:
            return playlist["id"]

    return -1

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

    return all_tracks

def dump_json(contents, json_filepath):
    with open(json_filepath, "w", encoding="utf-8") as file:
        json.dump(contents, file)

# creates a .vdjfolder file from a playlist_id
def create_vdjfolder_from_playlist(playlist_id, vdjfolder_filepath):
    # create the root and song entries
    root = ET.Element("VirtualFolder", noDuplicates="no")
    playlist_tracks = get_all_playlist_tracks(playlist_id, "output/sldl.json")
    processed_songs = process_music_dir()

    # for each track in the playlist, find its filepath and create an xml sub element with the info vdj needs
    for i, track in enumerate(playlist_tracks):
        spotify_title = track["track"]["name"]
        spotify_artists = ", ".join([artist["name"] for artist in track["track"]["artists"]])

        # if the song was found in the MUSIC_DIR dict, create an xml subelement with the info vdj needs, if it wasnt found, use spotify info and a palceholder filepath
        if spotify_title.lower() in processed_songs:
            metadata_title, metadata_artist, song_path = processed_songs[spotify_title.lower()]
            ET.SubElement(root, "song", path=song_path, title=metadata_title, artist=metadata_artist, idx=str(i))
        else:
            # TODO: need a better way of indexing the dictionary, there are files that exist that are not being found because of non-identical titles
            ET.SubElement(root, "song", path="Not Found", title=spotify_title, artist=spotify_artists, idx=str(i))
            
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

def process_music_dir():
    processed_songs = {}

    # for each file in the MUSIC_DIR, extract its metadata and add it to the dict
    for filename in os.listdir(MUSIC_DIR):
        filepath = os.path.join(MUSIC_DIR, filename)

        if not os.path.isfile(filepath):
            continue

        try:
            audio = TinyTag.get(filepath)

            if audio.title and audio.artist:
                processed_songs[audio.title.lower()] = (audio.title, audio.artist, filepath)
                # print("Title:" + audio.title) 
                # print("Artist: " + audio.artist)
                # print("Genre:" + audio.genre) 
                # print("Year Released: " + audio.year) 
                # print("Bitrate:" + str(audio.bitrate) + " kBits/s") 
                # print("Composer: " + audio.composer) 
                # print("Filesize: " + str(audio.filesize) + " bytes") 
                # print("AlbumArtist: " + audio.albumartist) 
                # print("Duration: " + str(audio.duration) + " seconds") 
                # print("TrackTotal: " + str(audio.track_total))  
            else:
                # TODO: add metadata with information from spotify 
                print(f"No metadata found for {filename}")
        except Exception as e:
            print(f"Error when reading metadata of {filename}: {e}")

    return processed_songs

if __name__ == "__main__":
    main()
