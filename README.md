# VDJ Spotify Link
This project builds on top of [SLDL](https://github.com/fiso64/slsk-batchdl), a tool to automate downloading large volumes of music from SoulSeek. 

# Installation
Clone the repo:
```bash
git clone https://github.com/jwapico/VDJ-Spotify-Link.git
cd VDJ-Spotify-Link
```

Create a python virtual environment:
```bash
python -m venv venv
```

Source the virtual environment:  
```bash
# For Windows:
venv/Scripts/Activate.ps1
```
```bash
# For Linux:
source venv/bin/activate
```

Install dependencies:
```bash
pip install -r requirements.txt
```

You will also need to update some lines in `assets/sldl_TEMPLATE_.conf` with your SoulSeek login and Spotify Auth info. Instructions for obtaining Spotify Auth can be found [here](https://github.com/fiso64/slsk-batchdl?tab=readme-ov-file#using-credentials). Once you're done, rename that file to just `assets/sldl.conf`

# Usage
To use the script, just run main.py with a link to your spotify playlist, and an optional output path:
```bash
python src/main.py <spotify playlist url> <output dir>
```


```
usage: main.py [-h] [--playlist-url PLAYLIST_URL] [--output-path OUTPUT_PATH] [pos_playlist_url] [pos_output_path]

A tool to download Spotify playlists using SoulSeek and SLDL

positional arguments:
  pos_playlist_url      The URL of the Spotify playlist to download
  pos_output_path       The output directory in which your files will be downloaded

options:
  -h, --help            show this help message and exit
  --playlist-url PLAYLIST_URL
                        The URL of the Spotify playlist to download
  --output-path OUTPUT_PATH
                        The output directory in which your files will be downloaded
```
