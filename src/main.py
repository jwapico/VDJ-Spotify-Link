import subprocess
import os
import argparse

def main():
	parser = argparse.ArgumentParser(description="A tool to download Spotify playlists using SoulSeek and SLDL")

	parser.add_argument("pos_playlist_url", nargs="?", help="The URL of the Spotify playlist to download")
	parser.add_argument("--playlist-url", dest="playlist_url", help="The URL of the Spotify playlist to download")

	parser.add_argument("pos_output_path", nargs="?", default=os.getcwd(), help="The output directory in which your files will be downloaded")
	parser.add_argument("--output-path", dest="output_path", help="The output directory in which your files will be downloaded")

	SLDL_EXE_PATH = os.path.join(os.path.dirname(os.path.abspath(__file__)), "../bin/sldl.exe")
	INDEX_FIXER_PY_PATH = os.path.join(os.path.dirname(os.path.abspath(__file__)), "index_fixer.py")

	args = parser.parse_args()
	PLAYLIST_URL = args.playlist_url or args.pos_playlist_url
	OUTPUT_PATH = args.output_path or args.pos_output_path

	if not PLAYLIST_URL:
		parser.error("The playlist URL is required")

	sldl_command = [SLDL_EXE_PATH, PLAYLIST_URL, "--path", OUTPUT_PATH, "--profile", "spotify-likes"]
	index_fixer_command = ["python", INDEX_FIXER_PY_PATH]

	subprocess.run(sldl_command)
	subprocess.run(index_fixer_command)

if __name__ == "__main__":
	main()