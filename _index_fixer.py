import os 
import shutil

def main():
	print("For best results, run this script from the same directory in which you ran sldl.")

	CURRENT_DIR = os.getcwd()
	subfolders = [item for item in os.listdir(CURRENT_DIR) if os.path.isdir(os.path.join(CURRENT_DIR, item))]
	sldl_subfolder = subfolders[0]

	if len(subfolders) == 1:
		old_sldl_index_filepath = sldl_subfolder + "\\_index.sldl"
	else:
		old_sldl_index_filepath = input("Could not find _index.sldl automatically, please enter its path: ")

	# TODO: keep track of history instead of overwriting the previous file every time
	old_filepath = sldl_subfolder + "\\OLD-SLDL-GENERATED_index.sldl"
	if not os.path.exists(old_filepath):
		os.rename(old_sldl_index_filepath, old_filepath)
	else:
		os.remove(old_filepath)
		os.rename(old_sldl_index_filepath, old_filepath)


	if os.path.exists(CURRENT_DIR + "\\sldl-helper_index.sldl"):
		new_sldl_index_filepath = CURRENT_DIR + "\\sldl-helper_index.sldl"
	else: 
		new_sldl_index_filepath = input("Could not find sldl-helper_index.sldl automatically, please enter its path: ")

	shutil.copy(new_sldl_index_filepath, sldl_subfolder + "\\_index.sldl")

	print("Done.")

if __name__ == "__main__":
	main()