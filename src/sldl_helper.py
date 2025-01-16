import sys
import subprocess
from datetime import datetime
import re
import os
import csv
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

# path configuration, the script creates a new sldl_helper directory in the same directory sldl was ran in
# sldl_helper/ contains the log file, the custom _index.sldl, and an _index_history directory thats used to track the sldl generated _index files (though this directory is created by index_fixer.py)
OUTPUT_PATH = os.getcwd()
SLDL_HELPER_DIR = OUTPUT_PATH + "\\sldl_helper\\"
os.makedirs(SLDL_HELPER_DIR, exist_ok=True)
LOG_FILEPATH = SLDL_HELPER_DIR + "sldl_helper.log"
CUSTOM_INDEX_FILEPATH = SLDL_HELPER_DIR + "_index.sldl"

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

    # if our custom _index.sldl file doesn't already exist, create it with the header
    if not os.path.exists(CUSTOM_INDEX_FILEPATH):
        with open(CUSTOM_INDEX_FILEPATH, "w", encoding="utf-8") as file:
            file.write("filepath,artist,album,title,length,tracktype,state,failurereason\n")

    # if sldl was able to find and download the song on SoulSeek, create the appropriate index entry
    if sldl_state == "Downloaded" or path != "":
        log_contents = ""
        seperator = "=" * 150
        timestamp = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
        sldl_index_entry = create_sldl_index_entry(path, artist, album, title, length)
        log_contents += (
            f"Downloading from SoulSeek...\n"
            f"Title: {title}\n"
            f"Artist: {artist}\n"
            f"Spotify URI: {uri}\n"
            f"Time: {timestamp}\n"
            f"Filepath: '{path}'\n"
            f"SLDL Index Entry: {sldl_index_entry}\n\n"
            f"{seperator}\n\n"
        )
        append_log_contents(log_contents)

    # if sldl did not find the song, download it from youtube
    elif sldl_state == "Failed":
        download_path = download_song_ytdlp(title, artist, uri, album, length)
        sldl_index_entry = create_sldl_index_entry(download_path, artist, album, title, length)

    # if there was a different state, the download likely failed
    else:
        sldl_index_entry = create_sldl_index_entry("", artist, album, title, length)
        log_contents = ""
        seperator = "=" * 150
        timestamp = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
        log_contents = (
            f"Tried to download from SoulSeek and yt-dlp...\n"
            f"Title: {title}\n"
            f"Artist: {artist}\n"
            f"Spotify URI: {uri}\n"
            f"Time: {timestamp}\n\n"
            f"DOWNLOAD FAILED - unexpected state: {sldl_state}\n\n"
            f"{seperator}\n\n"
        )
        append_log_contents(log_contents)

    # update_index_file(sldl_index_entry)
    # # get the contents of the file to see if it already contains our new index entry
    # with open(index_filepath, "r", encoding="utf-8") as index_file:
    #     lines = index_file.read()

    # # append the new entry to the end of the custom index file if its not already there
    # # TODO: if the download was successfull, we should check if an entry with the same song artist etc exists that failed. if there is one we should delete it
    # with open(index_filepath, "a", encoding="utf-8") as index_file:
    #     if lines.count(new_index_entry) == 0:
    #         index_file.write(f"{new_index_entry}\n")


# downloads the song with title and artist from youtube using yt-dlp, writes logging information to a log file
def download_song_ytdlp(title: str, artist: str, uri: str, album: str, length: str) -> str :
    search_query = f"ytsearch:{title} {artist}".encode("utf-8").decode()
    log_content = ""
    ytdlp_output = ""

    # TODO: fix empty queries with non english characters ctrl f '大掃除' in sldl_helper.log 

    # append the logfile with a timestamp, track info, and yt-dlp output and print it
    timestamp = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    log_content += (
        f"Downloading from yt-dlp...\n"
        f"Title: {title}\n"
        f"Artist: {artist}\n"
        f"Spotify URI: {uri}\n"
        f"Time: {timestamp}\n"
        f"Query: {search_query}\n\n"
    )

    # download the file using yt-dlp and necessary flags
    process = subprocess.Popen([
        "yt-dlp",
        search_query,
        "--cookies-from-browser", "firefox",
        "-x", "--audio-format", "mp3",
        "--embed-thumbnail", "--add-metadata",
        "--paths", OUTPUT_PATH,
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
    file_path_pattern = r'\[EmbedThumbnail\] ffmpeg: Adding thumbnail to "([^"]+)"'
    match = re.search(file_path_pattern, ytdlp_output)
    download_path = match.group(1) if match else ""

    # this extracts the title and artist from the yt-dlp output
    title_artist_pattern = r'\[download\] Finished downloading playlist: (.+)'
    match = re.search(title_artist_pattern, ytdlp_output)
    extracted_text = match.group(1).lower()

    # if our expected title or artist was not found in that text, the file is likely wrong and we want to log this
    if not title.lower() in extracted_text.lower():
        log_content += f"\n\nTitle ({title}) not found in output: {extracted_text}\n\n"
    if not artist.lower() in extracted_text.lower():
        log_content += f"\n\nArtist ({artist}) not found in output: {extracted_text}\n\n"         

    sldl_index_entry = create_sldl_index_entry(download_path, artist, album, title, length)

    seperator = "=" * 150
    failed_string = "\nDOWNLOAD FAILED - path empty\n"
    log_content += (
        f"\nFilepath: '{download_path}'\n"
        f"SLDL Index Entry: {sldl_index_entry}\n"
        f"{failed_string if download_path == '' else ''}"
        f"\n{seperator}\n\n"
    )
    append_log_contents(log_content)

    return download_path

# this creates an entry for the _index.sldl file for a given song
def create_sldl_index_entry(filepath, artist, album, title, length):
    sldl_index_entry_dict = {
        filepath: filepath,
        artist: artist,
        album: album,
        title: title,
        length: length,
    }

    # since we are using double quotes to enclose strings, we cant have them in the string itself
    sldl_index_entry_dict = {
        key: (value.replace('"', "'") if isinstance(value, str) else value)
        for key, value in sldl_index_entry_dict.items()
    }

    # if our values are not the correct type, sldl will throw an error. we need to check everything because the metadata provided by soulseek users may be incorrect
    if not isinstance(filepath, str):
        sldl_index_entry_dict[filepath] = ""

    if not isinstance(artist, str):
        sldl_index_entry_dict[artist] = ""

    if not isinstance(album, str):
        sldl_index_entry_dict[album] = ""

    if not isinstance(title, str):
        sldl_index_entry_dict[title] = ""

    if not length.isdigit():
        sldl_index_entry_dict[length] = -1

    # filepath,artist,album,title,length,tracktype,state,failurereason
    if filepath == "":
        sldl_index_entry = f'"","{sldl_index_entry_dict[artist]}","{sldl_index_entry_dict[album]}","{sldl_index_entry_dict[title]}",{sldl_index_entry_dict[length]},0,2,3'
    else:
        sldl_index_entry = f'"{sldl_index_entry_dict[filepath]}","{sldl_index_entry_dict[artist]}","{sldl_index_entry_dict[album]}","{sldl_index_entry_dict[title]}",{sldl_index_entry_dict[length]},0,1,0'

    # get the contents of the previous index file
    with open(CUSTOM_INDEX_FILEPATH, "r", encoding="utf-8") as index_file:
        old_index_lines = index_file.readlines()

    new_index_entries = []
    # if the index file is empty, we need to initialize it with the header and our new entry
    if len(old_index_lines) == 0:
        new_index_entries.append("filepath,artist,album,title,length,tracktype,state,failurereason\n")
        new_index_entries.append(sldl_index_entry + "\n")
    else:
        # for each line in the previous index file, append it to the new lines if its not an identical failed download, and it's not already present
        for i, old_entry in enumerate(old_index_lines):
            # always want the header
            if i == 0:
                new_index_entries.append(old_entry)
            else:
                # csv.DictReader reads the plaintext line into a dictionary mapping each item in the header to its corresponding value. we index by -1 because it does not include the header
                entry_dicts = list(csv.DictReader(old_index_lines))
                old_entry_dict = entry_dicts[i - 1]
                # if the current download succeeded (non-empty filepath) and the previous attempts at downloading the track failed, we don't want to include the old failed entry since sldl will try to redownload it everytime
                remove_identical_failed_download = old_entry_dict["title"] == title and old_entry_dict["artist"] == artist and old_entry_dict["album"] == album and int(old_entry_dict["state"]) == 2 and filepath != ""

                # we also don't want to include duplicate entries
                if not remove_identical_failed_download:
                    new_index_entries.append(old_entry)

        # after adding all the previous entries, we can append the new one if it's not a duplicate
        if not sldl_index_entry in "\n".join(new_index_entries):
            new_index_entries.append(sldl_index_entry + "\n")

    # now we can finally rewrite the old file with our new entries
    with open(CUSTOM_INDEX_FILEPATH, "w", encoding="utf-8") as file:
        file.writelines(new_index_entries)

    return sldl_index_entry

# returns true if the new log contents are already in the log file
def check_duplicate_log_content(new_log_contents: str) -> bool :
    if os.path.exists(LOG_FILEPATH):
        with open(LOG_FILEPATH, "r", encoding="utf-8") as log_file:
            file_contents = log_file.read()

            # we need to remove the timestamps to check for equality
            timestamp_pattern = r"Time: \d{4}-\d{2}-\d{2} \d{2}:\d{2}:\d{2}"
            file_contents_no_timestamp = re.sub(timestamp_pattern, "", file_contents)
            log_contents_no_timestamp = re.sub(timestamp_pattern, "", new_log_contents)

            if log_contents_no_timestamp in file_contents_no_timestamp:
                return True
            
            return False
    else:
        raise FileNotFoundError(f"File doesn't exist: {LOG_FILEPATH}")

# appends the new log contents to the log file
def append_log_contents(new_log_contents: str) -> None :
    # if the log_content is already in the file, we don't want to add it again because it would be harder to search for failed downloads since theyd be appended to the file multiple times
    with open(LOG_FILEPATH, "a", encoding="utf-8") as log_file:
        if check_duplicate_log_content(new_log_contents) == False:
            log_file.write(new_log_contents)


if __name__ == "__main__":
    try:
        main()
    except Exception as e:
        error_message = traceback.format_exc()
        input(f"error moment: {error_message}")