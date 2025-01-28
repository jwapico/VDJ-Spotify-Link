import subprocess
import os
import argparse

# this file controls the flow of the program. it first calls sldl.exe using the passed in arguments
# sldl then automatically runs sldl_helper.py for each song it downloads (or fails to download)
# then we run index_fixer.py which updates _index.sldl to reflect songs that were successfully downloaded from yt so sldl doesn't try to download them again

def main():
	# initialize the arg parser
	parser = argparse.ArgumentParser(description="A tool to download Spotify playlists using SoulSeek and SLDL")
	parser.add_argument("pos_playlist_url", nargs="?", help="The URL of the Spotify playlist to download")
	parser.add_argument("--playlist-url", dest="playlist_url", help="The URL of the Spotify playlist to download")
	parser.add_argument("pos_output_path", nargs="?", default=os.getcwd(), help="The output directory in which your files will be downloaded")
	parser.add_argument("--output-path", dest="output_path", help="The output directory in which your files will be downloaded")

	# path config is all relative to the path to this file
	SLDL_EXE_PATH = os.path.join(os.path.dirname(os.path.abspath(__file__)), "../assets/sldl.exe")
	INDEX_FIXER_PATH = os.path.join(os.path.dirname(os.path.abspath(__file__)), "index_fixer.py")

	# parse the arguments and update sldl.conf with the output path
	args = parser.parse_args()
	PLAYLIST_URL = args.playlist_url or args.pos_playlist_url
	OUTPUT_PATH = os.path.abspath(args.output_path or args.pos_output_path)
	update_sldl_conf(OUTPUT_PATH)

	if not PLAYLIST_URL:
		parser.error("The playlist URL is required")

	# create and run the commands 
	sldl_command = [SLDL_EXE_PATH, PLAYLIST_URL, "--path", OUTPUT_PATH, "--profile", "spotify-likes"]
	index_fixer_command = ["python", INDEX_FIXER_PATH, OUTPUT_PATH]
	subprocess.run(sldl_command)
	subprocess.run(index_fixer_command)

# this function updates the on-complete line in sldl.conf to pass in the user specified output path to sldl_helper.py
def update_sldl_conf(new_output_path):
	SLDL_CONF_PATH = os.path.join(os.path.dirname(os.path.abspath(__file__)), "../assets/sldl.conf")

	with open(SLDL_CONF_PATH, "r", encoding="utf-8") as conf_file:
		lines = conf_file.readlines()

	# we want to modify the line in sldl.conf that starts with 'on-complete = s:python'
	sldl_helper_line = next((line for line in lines if line.startswith('on-complete = s:python')), None).split(" ")
	if sldl_helper_line is None:
		raise Exception('Could not find the correct on-complete line in sldl.conf. Please add the following line to your sldl.conf: on-complete = s:python "your-path-to\sldl_helper.py" "{path}" "{title}" "{artist}" "{album}" "{uri}" "{length}" "{failure-reason}" "{state}"')

	new_lines = lines

	# if the final item on that line is state, we have not modified sldl.conf, so we need to add the output path to the line, otherwise we want to swap the old path for the new one
	if sldl_helper_line[-1] == '"{state}"\n':
		sldl_helper_line[-1] = sldl_helper_line[-1].replace('\n', "")
		new_sldl_helper_line = sldl_helper_line + [f'"{new_output_path}"\n']
		new_lines[-1] = " ".join(new_sldl_helper_line)
	else:
		sldl_helper_line[-1] = f'"{new_output_path}"\n'
		new_lines[-1] = " ".join(sldl_helper_line)

	# write back the new lines
	with open(SLDL_CONF_PATH, "w", encoding="utf-8") as conf_file:
		conf_file.writelines(new_lines)

if __name__ == "__main__":
	main()