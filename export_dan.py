
from PIL import Image
import json
import os
import os.path
from tqdm import tqdm

import data
import tagger
import sys
import danbooru



files = danbooru.getFiles()
ids = files.keys()

out_folder = 'out_emi'
filter_tags = ['yusa_emi']
avoid_tags = []

textual_inversion_tag = None
do_random = False

if not os.path.exists(out_folder):
	os.makedirs(out_folder)

def hasTag(id, wanted_tag):
	(_, image_path, data) = danbooru.getPostInfo(id)
	
	tags = data[0]['tags']
	
	for tag in wanted_tag:
		if tag in tags:
			return True
	return False
	

if do_random:
	ids = random.choices(ids, k=200)

if textual_inversion_tag:
	ids = [x for x in ids if hasTag(x, [textual_inversion_tag])]

if len(filter_tags) > 0:
	ids = [x for x in ids if hasTag(x, filter_tags)]
if len(avoid_tags) > 0:
	ids = [x for x in ids if not hasTag(x, avoid_tags)]

def split_image(id, image_name):
	base_prompt = danbooru.get_prompt(id).replace('(', '\\(').replace(')', '\\)')

	# Save each of the selected tiles as an image with the filename from the original file
	base, ext = os.path.splitext(os.path.basename(image_name))
	tile_path = f"{out_folder}/{base}"
	print(tile_path)
	#os.symlink(os.path.abspath(image_name), f"{tile_path}{ext}")

	# Save a text file with the coordinates of the tile
	with open(f"{tile_path}.txt", "w") as f:
		f.write(base_prompt)

if __name__ == "__main__":
	
	for id in tqdm(ids):
		split_image(id, files[id])
