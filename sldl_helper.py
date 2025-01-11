import sys
import subprocess
from datetime import datetime
import re
import os
import traceback

# https://github.com/fiso64/slsk-batchdl

# this script is automatically ran by sldl after attempting to download a song (whether the download was successfull or not)
# if the download was successfull, this script will update a log file and custom _index.sldl file with the relevant information
# if the download was unsuccessfull, it will try to download the song from youtube using yt-dlp, and update the log file and custom _index.sldl file accordingly

# IMPORTANT NOTES: 
#   - you need to add this line to your sldl.conf file:
#       on-complete = s:python "your-path-to\sldl_helper.py" "{path}" "{title}" "{artist}" "{album}" "{uri}" "{length}" "{failure-reason}" "{state}"
#   - yt-dlp and python also need to be globally accessible from the terminal
#   - if using playlists from spotify, you will need to add authentication information to sldl.conf as well, see the slsk-batchdl github above

def main():
    # info fed to the script by sldl
    path = sys.argv[1]
    title = sys.argv[2]
    artist = sys.argv[3]
    album = sys.argv[4]
    uri = sys.argv[5]
    length = sys.argv[6]
    failure_reason = sys.argv[7]
    sldl_state = sys.argv[8]

    # path configuration, the script creates a new sldl-helper directory in the same directory sldl was ran in
    # this directory contains the log file, the custom _index.sldl, and an _index_history directory thats used to track the sldl generated _index files (though this directory is created by _index_fixer.py)
    OUTPUT_PATH = os.getcwd()
    SLDL_HELPER_PATH = OUTPUT_PATH + "\\sldl_helper"
    os.makedirs(SLDL_HELPER_PATH, exist_ok=True)
    LOG_FILE_PATH = f"{SLDL_HELPER_PATH}\\sldl_helper.log"
    NEW_INDEX_FILEPATH = F"{SLDL_HELPER_PATH}\\_index.sldl"

    # if our custom _index.sldl file doesn't already exist, create it with the header
    if not os.path.exists(NEW_INDEX_FILEPATH):
        with open(NEW_INDEX_FILEPATH, "w", encoding="utf-8") as file:
            file.write("filepath,artist,album,title,length,tracktype,state,failurereason\n")

    # if sldl was able to find and download the song on SoulSeek, create the appropriate index entry
    # sldl expects index entries to look like this: filepath,artist,album,title,length,tracktype,state,failurereason
    if sldl_state == "Downloaded":
        log_contents = ""
        seperator = "=" * 150
        timestamp = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
        sldl_index_entry = f'"{path}","{artist}","{album}","{title}",{length},{0},{1},{0}'
        log_contents += f"""
Downloaded from SoulSeek...
Title: {title}
Artist: {artist}
Spotify URI: {uri}
Time: {timestamp}
Filepath: '{path}'
SLDL Index Entry: {sldl_index_entry}

{seperator}
"""
        append_log_contents(log_contents, LOG_FILE_PATH)

    # if sldl did not find the song, download it from youtube
    elif sldl_state == "Failed":
        download_path = download_song_ytdlp(title, artist, uri, album, length, OUTPUT_PATH, LOG_FILE_PATH)
        
        # if the download was successfull extract the filepath from the yt-dlp output and build the correct index entry, if it wasnt, we want the path to be empty and the state field to be 2 (Failed)
        if download_path != "":
            sldl_index_entry = f'"{download_path}","{artist}","{album}","{title}",{length},0,1,0'
        else:
            sldl_index_entry = f'"","{artist}","{album}","{title}",{length},0,2,3'

    # if there was a different state, the download likely failed
    else:
        sldl_index_entry = f'"","{artist}","{album}","{title}",{length},0,2,3'
        log_contents = ""
        seperator = "=" * 150
        timestamp = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
        log_contents = f"""
Tried to download from SoulSeek and yt-dlp...
Title: {title}
Artist: {artist}
Spotify URI: {uri}
Time: {timestamp}

Download failed with unexpected state: {sldl_state}

{seperator}
"""
        append_log_contents(log_contents, LOG_FILE_PATH)

    # get the contents of the file to see if it already contains our new index entry
    with open(NEW_INDEX_FILEPATH, "r", encoding="utf-8") as index_file:
        lines = index_file.read()

    # append the new entry to the end of the custom index file if its not already there
    with open(NEW_INDEX_FILEPATH, "a", encoding="utf-8") as index_file:
        if lines.count(sldl_index_entry) == 0:
            index_file.write(f"{sldl_index_entry}\n")

# returns true if the new log contents are already in the log file
def check_duplicate_log_content(new_log_contents: str, log_filepath: str) -> bool :
    if os.path.exists(log_filepath):
        with open(log_filepath, "r", encoding="utf-8") as log_file:
            file_contents = log_file.read()

            # we need to remove the timestamps to check for equality
            timestamp_pattern = r"Time: \d{4}-\d{2}-\d{2} \d{2}:\d{2}:\d{2}"
            file_contents_no_timestamp = re.sub(timestamp_pattern, "", file_contents)
            log_contents_no_timestamp = re.sub(timestamp_pattern, "", new_log_contents)

            if log_contents_no_timestamp in file_contents_no_timestamp:
                return True
            
            return False
    else:
        raise FileNotFoundError(f"File doesn't exist: {log_filepath}")

# appends the new log contents to the log file
def append_log_contents(new_log_contents: str, log_filepath: str) -> None :
    # if the log_content is already in the file, we don't want to add it again because it would be harder to search for failed downloads since theyd be appended to the file multiple times
    with open(log_filepath, "a", encoding="utf-8") as log_file:
        if check_duplicate_log_content(new_log_contents, log_filepath) == False:
            log_file.write(new_log_contents)

# downloads the song with title and artist from youtube using yt-dlp, writes logging information to a log file
def download_song_ytdlp(title: str, artist: str, uri: str, album: str, length: str, output_path: str, log_filepath: str) -> str :
    search_query = f"ytsearch:{title} {artist}"
    log_content = ""
    ytdlp_output = ""

    # append the logfile with a timestamp, track info, and yt-dlp output and print it
    with open(log_filepath, "a", encoding="utf-8") as log:
        timestamp = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
        log_content += f"""
Downloading from yt-dlp...
Title: {title}
Artist: {artist}
Spotify URI: {uri}
Time: {timestamp}
Query: {search_query}

"""
        # download the file using yt-dlp and necessary flags
        process = subprocess.Popen([
            "yt-dlp",
            search_query,
            "--cookies-from-browser", "firefox",
            "-x", "--audio-format", "mp3",
            "--embed-thumbnail", "--add-metadata",
            "--paths", output_path,
            "-o", f"{title} - {artist}.%(ext)s"
        ], stdout=subprocess.PIPE, stderr=subprocess.STDOUT, text=True)

        # print and append the output of yt-dlp to the log file
        for line in iter(process.stdout.readline, ''):
            print(line, end='')
            log_content += line
            ytdlp_output += line

        process.stdout.close()
        process.wait()

        # this extracts the filepath of the new file from the yt-dlp output
        if ytdlp_output.count(f"[download] Finished downloading playlist: {title} {artist}") > 0:
            file_path_pattern = r'\[EmbedThumbnail\] ffmpeg: Adding thumbnail to "([^"]+)"'
            match = re.search(file_path_pattern, ytdlp_output)
            download_path = match.group(1) if match else ""
        else:
            download_path = ""

        # this extracts the title and artist from the yt-dlp output
        title_artist_pattern = r'\[download\] Finished downloading playlist: (.+)'
        match = re.search(title_artist_pattern, ytdlp_output)
        extracted_text = match.group(1).lower()

        # if our expected title or artist was not found in that text, the file is likely wrong and we want to log this
        if not title.lower() in extracted_text.lower():
            log_content += f"\n\nTitle ({title}) not found in output: {extracted_text}\n\n"
        if not artist.lower() in extracted_text.lower():
            log_content += f"\n\nArtist ({artist}) not found in output: {extracted_text}\n\n"         

        # add relevant info the log contents
        sldl_index_entry = f'"{download_path}","{artist}","{album}","{title}",{length},0,1,0'
        seperator = "=" * 150
        log_content += f"""
Filepath: '{download_path}'
SLDL Index Entry: {sldl_index_entry}

{seperator}
        """
        
        append_log_contents(log_content, log_filepath)

        return download_path

if __name__ == "__main__":
    try:
        main()
    except Exception as e:
        error_message = traceback.format_exc()
        input(f"error moment: {error_message}")