import sys
import subprocess
from datetime import datetime
import re
import os
import shutil

# https://github.com/fiso64/slsk-batchdl

# downloads the song with title and artist from youtube using yt-dlp, writes logging information to a log file
def download_song(title, artist, uri, album, length, output_path, log_file):
    search_query = f"ytsearch:{title} {artist}"
    ytdlp_output = ""

    # append the logfile with a timestamp, track info, and yt-dlp output and print it
    with open(log_file, "a") as log:
        timestamp = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
        log.write(f"Downloading from yt-dlp...\nTitle: {title}\nArtist: {artist}\nSpotify URI: {uri}\nTime: {timestamp}\nQuery: {search_query}\n\n")

        process = subprocess.Popen([
            "yt-dlp",
            search_query,
            "--cookies-from-browser", "firefox",
            "-x", "--audio-format", "mp3",
            "--embed-thumbnail", "--add-metadata",
            "--paths", output_path,
            "-o", f"%(title)s - %(artist)s.%(ext)s"
        ], stdout=subprocess.PIPE, stderr=subprocess.STDOUT, text=True)

        for line in iter(process.stdout.readline, ''):
            print(line, end='')
            log.write(line)
            ytdlp_output += line

        process.stdout.close()
        process.wait()

        if ytdlp_output.count(f"[download] Finished downloading playlist: {title} {artist}") > 0:
            file_path_pattern = r'\[EmbedThumbnail\] ffmpeg: Adding thumbnail to "([^"]+)"'
            match = re.search(file_path_pattern, ytdlp_output)
            download_path = match.group(1) if match else ""
        else:
            download_path = ""

        sldl_index_entry = f'"{download_path}",{artist},{album},{title},{length},0,1,0'
        seperator = "=" * 150
        log.write(f"\nFilepath: '{download_path}'")
        log.write(f"\nSLDL Index Entry: {sldl_index_entry}")
        log.write(f"\n\n{seperator}\n\n")

        return download_path

def main():
    # check that the number of arguments is correct
    if len(sys.argv) != 9:
        print('"D:\DJ\Software\SoulSeek\on-complete.py" "{path}" "{title}" "{artist}" "{album}" "{uri}" "{length}" "{failure-reason}" "{state}"')
        raise Exception(f'Incorrect number of arguments ({len(sys.argv)}), expected 9. Correct format should be: \n"D:\DJ\Software\SoulSeek\on-complete.py" path" title" artist" album" uri" length" failure-reason" state"\nPlease check sldl.conf')

    # info fed to the script by sldl
    path = sys.argv[1]
    title = sys.argv[2]
    artist = sys.argv[3]
    album = sys.argv[4]
    uri = sys.argv[5]
    length = sys.argv[6]
    failure_reason = sys.argv[7]
    state = sys.argv[8]

    OUTPUT_PATH = os.getcwd()
    # TODO: put these in sldl-helper folder so they arent cluttering the music directory. also make them accessible to _index_fixer.py
    LOG_FILE_PATH = f"{OUTPUT_PATH}\\sldl-helper.log"
    NEW_INDEX_FILEPATH = F"{OUTPUT_PATH}\\sldl-helper_index.sldl"

    # if our custom _index.sldl file doesn't already exist, create it with the header
    if not os.path.exists(NEW_INDEX_FILEPATH):
        with open(NEW_INDEX_FILEPATH, "w") as file:
            file.write("filepath,artist,album,title,length,tracktype,state,failurereason\n")
        print(f"File {NEW_INDEX_FILEPATH} created with header.")

    # if sldl was able to find and download the song on SoulSeek, create the appropriate index entry
    # sldl expects index entries to look like this: filepath,artist,album,title,length,tracktype,state,failurereason
    if state == "Downloaded":
        sldl_index_entry = f'"{path}",{artist},{album},{title},{length},{0},{1},{0}'
        with open(LOG_FILE_PATH, "a") as log_file:
            timestamp = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
            log_file.write("Downloaded from SoulSeek...")
            log_file.write(f"\nTitle: {title}\nArtist: {artist}\nSpotify URI: {uri}\nTime: {timestamp}")
            log_file.write(f"\nFilepath: '{path}'")
            log_file.write(f"\nSLDL Index Entry: {sldl_index_entry}")
            seperator = "=" * 150
            log_file.write(f"\n\n{seperator}\n\n")
    # if sldl did not find the song, download it from youtube
    elif state == "Failed":
        download_path = download_song(title, artist, uri, album, length, OUTPUT_PATH, LOG_FILE_PATH)
        
        # if the download was successfull extract the filepath from the yt-dlp output and build the correct index entry
        if download_path != "":
            sldl_index_entry = f'"{download_path}",{artist},{album},{title},{length},0,1,0'
            print("DOWNLOAD SUCCESS")
        # if the download wasn't successfull from yt-dlp either, the index entry should reflect this
        else:
            sldl_index_entry = f'"",{artist},{album},{title},{length},0,2,3'
            print("DOWNLOAD FAIL")
    else:
        raise Exception(f"Unexpected state: {state}")

    # get the contents of the file to see if it already contains our new index entry
    with open(NEW_INDEX_FILEPATH, "r") as index_file:
        lines = index_file.read()

    # append the new entry to the end of the custom index file if its not already there
    with open(NEW_INDEX_FILEPATH, "a") as index_file:
        if lines.count(sldl_index_entry) == 0:
            index_file.write(f"{sldl_index_entry}\n")

if __name__ == "__main__":
    try:
        main()
    except Exception as e:
        print(e)
        # TODO: logging here too
        input("\n\nError occured, press enter to close")
    finally:
        pass
