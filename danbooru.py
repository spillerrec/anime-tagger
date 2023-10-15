import os
import data
import requests
import time
import pathlib
import glob
import json

	
hypertags = data.readJsonIf('workdir/hypertags.json', {})
replace_tags = data.readJsonIf('workdir/replace_tags.json', [])
dan_tags = data.readJsonIf('workdir/danbooru.json')
extra_tags = data.readJsonIf('workdir/extra_tags.json', [])
remove_tags = data.readJsonIf('workdir/remove_tags.json', [])


def getPostInfo(id_str):
	prefix = 'dan_'
	id_str_full = id_str
	if id_str.startswith('dan_'):
		id_str = id_str[4:]
		
	json_path = 'workdir/posts/%s.json' % (id_str,)
		
	if id_str.startswith('san_'):
		id_str = id_str[4:]
		prefix = 'san_'
		
		
	has_post = os.path.exists(json_path)
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
	
	tags = jsonData[0]['tags'].split(' ')
	for tag in extra_tags.keys():
		if id_str in extra_tags[tag]:
			if extra_tags[tag][id_str]:
				tags = tags + [tag]
			else:
				tags = [x for x in tags if x != tag]
	for tag in remove_tags:
		if tag in tags:
			tags = [x for x in tags if x != tag]
	jsonData[0]['tags'] = tags
		
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
	
def tagCount(tag):
	if tag in dan_tags:
		return dan_tags[tag]['count']
	return 0	
	

def get_prompt(id_str, textual_inversion_tag=None):
	(_, _, data) = getPostInfo(id_str)
	tags = list(set(data[0]['tags']))
	
	tags_path = id_str + '.txt'
	
	authors = []
	custom_tags = []
	kept_tags = []
	
	has_hypertags = []
	for tag in tags:
		if tag in hypertags['tags']:
			#print('Detected hypertag: ' + tag)
			has_hypertags = has_hypertags + [tag]
	print(has_hypertags)
	
	ignore_list = []
	
	#if len(has_hypertags) > 1 and random.choice([True, False]):
	#	picked_tag = random.choice(has_hypertags)
	#	print('Keeping only: ' + picked_tag)
	#	for tag in has_hypertags:
	#		if tag != picked_tag:
	#			ignore_list += [tag]
	#	has_hypertags = [picked_tag]
	
	for tag in has_hypertags:
		ignore_list = hypertags['tags'][tag]['remove'] + ignore_list
	
	if textual_inversion_tag:
		ignore_list += [textual_inversion_tag]
	
	# Remove tags which has low chance of being understood of the base model
	# This only works for the danbooru specialisation, the base SD training might understand some concepts better,
	# but I don't know if there is a way to take that into account
	for tag in tags:
		if tagCount(tag) < 800 and not tag in hypertags['tags']:
			ignore_list += [tag]
	
	for tag in tags:
		if not tag in ignore_list:
		
			for replacer in replace_tags:
				if replacer['from'][0] == tag:
					tag = replacer['to']
		
			#info = get_cached(tag)
			tag_name = tag.replace('_', ' ')
			kept_tags.append(tag_name)
			#if len(info) > 0:
			#	if info[0]['category'] == 1:
			#		authors.append(tag_name)
			#	else:
			#		kept_tags.append(tag_name)
			
	
	prompt = '';
	
	prompt += ', '.join(custom_tags + kept_tags)
	
	if len(authors) > 0:
		#prompt += ', in the style of ' + ' and '.join(authors) + ', '
		prompt +=  ', ' + ', '.join(authors)
	
	return prompt