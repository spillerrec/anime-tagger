import os
import data
import requests
import time
import pathlib
import glob

def getPostInfo(id_str):
	json_path = 'workdir/posts/%s.json' % (id_str,)
	has_post = os.path.exists(json_path)
	prefix = 'dan_'
	id_str_full = id_str
	if id_str.startswith('san_'):
		id_str = id_str[4:]
		prefix = 'san_'
	if not has_post:
		if prefix == 'san_':
			json_url = 'http://localhost:8000/json/san/%s/' % id_str
			print('downloading: ' + json_url)
			r = requests.get(json_url).text
			raw = r.split('\n')
			jsonData = [
				{
					#"has_comments":false,
					#"parent_id":null,
					#"status":"active",
					#"has_children":false,
					#"created_at":"2011-01-15 20:32:03",
					#"has_notes":false,
					#"rating":"s",
					#"author":"Mr_GT",
					#"creator_id":102191,
					#"width":1000,
					#"source":"https://...",
					#"score":12,
					"tags":raw[0],
					#"height":1300,
					#"file_size":509713,
					"id":int(id_str),
					"file_url": 'http://localhost:8000' + raw[1],
					#"preview_url":"https://....jpg",
					"md5":"325234..."
				}
			]
			with open(json_path, "w") as f:
				json.dump(jsonData, f, indent=2)
			
		else:
			json_url = 'https://danbooru.donmai.us/post/index.json?tags=id:' + id_str
			print('downloading: ' + json_url)
			r = requests.get(json_url).content
			open(json_path, 'wb').write(r)
			time.sleep(1)
	
	jsonData = data.readJson(json_path)
	image_url = jsonData[0]['file_url']
	
	image_suffix = pathlib.Path(image_url).suffix
	image_path = prefix + id_str + image_suffix
	
	jsonData[0]['tags'] = jsonData[0]['tags'].split(' ')
	#tags = jsonData[0]['tags'].split(' ')
	#for tag in extra_tags.keys():
	#	if id_str_full in extra_tags[tag]:
	#		if extra_tags[tag][id_str_full]:
	#			tags = tags + [tag]
	#		else:
	#			tags = [x for x in tags if x != tag]
	#for tag in remove_tags:
	#	if tag in tags:
	#		tags = [x for x in tags if x != tag]
	#jsonData[0]['tags'] = ' '.join(tags)
		
	return (id, image_path, jsonData)
	
	
def allDirs(path):
	return [f'{path}/{f}' for f in os.listdir(path) if os.path.isdir(f'{path}/{f}')]

def getFiles(path = 'workdir/danbooru'):
	map = {}
	for folder in allDirs(path):
		print(folder)
		for filename in os.listdir(folder):
			if filename.startswith('dan_') or filename.startswith('san_'):
				id = pathlib.Path(filename).stem
				type = pathlib.Path(filename).suffix
				if type != '.txt':
					print(id)
					map[id] = f'{folder}/{filename}'
			
	return map