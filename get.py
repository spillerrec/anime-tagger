import requests
import re
import os
import json
import pathlib
import time
import sys

import danbooru

def getIds(folder, filename = 'posts'):
	def extract_id(url):
		prefix = ''
		if url.startswith('http://localhost:8000/post/'):
			prefix = 'san_'
		#print(url)
		#print(re.findall(r"\/[0-9]+", url)[0][1:])
		return prefix + str(int(re.findall(r"\/[0-9]+", url)[0][1:])) #int to ensure we got something
	lines = []
	
	if not isinstance(folder, list):
		folder = [folder]
	
	for f in folder:
		with open('%s/%s.txt' % (f, filename)) as f:
			lines += f.readlines()

	return list(set(map(extract_id, lines)))

filename = 'posts'
if len(sys.argv) > 2:
	filename = sys.argv[2]
	
folder = 'workdir/danbooru/' + sys.argv[1]

ids = getIds(folder, filename)

for id in ids: #Safe keeping
	(_, image_path, data) = danbooru.getPostInfo(id)
	image_path = folder + '/' + image_path
	
	image_url = data[0]['file_url']
	
	has_image = os.path.exists(image_path)
	if not has_image:
		print('downloading: ' + image_url)
		open(image_path, 'wb').write(requests.get(image_url).content)
		time.sleep(1)
	
	