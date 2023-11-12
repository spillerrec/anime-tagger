import os
import os.path
import json
from PIL import Image
import tagger
import pathlib

def readJson(json_path):
	with open(json_path, encoding="utf-8") as json_file:
		return json.load(json_file)

def readJsonIf(path, default_value={}):
	if os.path.exists(path):
		return readJson(path)
	return default_value
	
currentSourceDir = ""
def setSourceDir(sourceDir):
	global currentSourceDir
	currentSourceDir = sourceDir
	
def getJsonPath(path):
	if currentSourceDir == "":
		raise "Source dir not set!"
	return 'images/' + currentSourceDir + '/' + path
	
def iterateDir(folderPath):
	files = []
	dirs = []
	for f in os.listdir(folderPath):
		fullPath = os.path.join(folderPath, f)
		if os.path.isfile(fullPath):
			if pathlib.Path(fullPath).suffix != ".json":
				files.append(fullPath)
		elif os.path.isdir(fullPath):
			dirs.append(fullPath)
		else:
			print("Unknown file: " + fullPath)
	return (files, dirs)
	
def getFiles(image_group):
	imagePathFull = 'images/' + image_group
	
	files, dirs = iterateDir(imagePathFull)
	for dir in dirs:
		filesSub, _ = iterateDir(dir)
		files = files + filesSub
		
	res = []
	for file in files:
		res.append(file[len('images/'):])
	
	return res
	
def getAreas():
	extra_tags = {}
	path = getJsonPath('area_tags.json')
	if os.path.exists(path):
		return readJson(path)
	return {}
	
def saveAreas(hypertags):
	path = getJsonPath('area_tags.json')
	with open(path, "w") as f:
		json.dump(hypertags, f, indent=2)
	
taggerCache = None
taggerCacheDirty = False
def getTaggerCache():
	global taggerCache
	path = getJsonPath('auto_tag_cache.json')
	if taggerCache:
		return taggerCache
	if os.path.exists(path):
		taggerCache = readJson(path)
		return taggerCache
	return {}
	
def saveTaggerCache(hypertags):
	global taggerCache
	global taggerCacheDirty
	taggerCacheDirty = True
	taggerCache = hypertags
		
def writeTaggerCache():
	global taggerCache
	global taggerCacheDirty
	if taggerCacheDirty:
		taggerCacheDirty = False
		path = getJsonPath('auto_tag_cache.json')
		with open(path, "w") as f:
			json.dump(taggerCache, f, indent=2)
	
def getCharacterTags():
	path = getJsonPath('character_tags.json')
	if os.path.exists(path):
		return readJson(path)
	return {}
	
def saveCharacterTags(hypertags):
	path = getJsonPath('character_tags.json')
	with open(path, "w") as f:
		json.dump(hypertags, f, indent=2)

	
def getIds(group):
	return [id for id, item in enumerate(getFiles(group))]
	
def getMissingIds(group):
	return list(filter(lambda x: len(getCrops(group, x)) == 0, getIds(group)))
	
def getImagePath(group, id):
	if '-' in id:
		id = id.split('-')[0]
	return 'images/' + getFiles(group)[int(id)]
	
def setCrop(group, id, rects):
	areas = getAreas()
	areas[group][id] = rects
	saveAreas(areas)
	
def getCrops(group, id):
	id = str(id)
	areas = getAreas()
	if not group in areas:
		return []
	if not id in areas[group]:
		return []
	return list(filter(cropIsValid, areas[group][id]))
	
def getCrop(group, id):
	areas = getAreas()
	
	items = id.split('-')
	key = items[0]
	index = int(items[1])
	return getCrops(group, key)[index]
	
def hasCrop(group, id):
	if getCrop(group, id):
		return True
	return False
	
def cropIsValid(rect):
	w = int(rect['width'])
	h = int(rect['height'])
	return w > 0 and h > 0
	
def getCropIds(group):
	areas = getAreas()
	if not group in areas:
		return []
	
	ids = []
	for key, rects in areas[group].items():
		for index, rect in enumerate(filter(cropIsValid, rects)):
			ids.append(key + '-' + str(index))
	return ids

def getCroppedImage(group, id):
	crop = getCrop(group, id)
	
	if crop:
		path = getImagePath(group, id)
		rect = crop
		img = Image.open(path).convert('RGBA')
		width, height = img.size
		
		if len(img.size) == 2:
			img = img.convert('RGBA')
		
		#Remove alpha
		background = Image.new('RGBA', img.size, (255,255,255))
		img = Image.alpha_composite(background, img).convert('RGB')
			
		
		x = max(0, int(rect['x']))
		y = max(0, int(rect['y']))
		w = int(rect['width'])
		h = int(rect['height'])
		w = min(width, x+w) - x
		h = min(height, y+h) - y
		
		if w > 0 and h > 0:
			return img.crop((x, y, x + w, y + h))
	return None
		
def getAutoTags(group, id):
	cache = getTaggerCache()
	
	if group in cache:
		if id in cache[group]:
			return cache[group][id]
	else:
		cache[group] = {}
	
	cropped = getCroppedImage(group, id)
	tagResult = tagger.evaluate(cropped)
	
	cache[group][id] = tagResult.tolist()
	saveTaggerCache(cache)
	
	return tagResult
	
def hasManualTag(group, id, tag):
	charaTags = getCharacterTags()
	
	if not group in charaTags:
		return False
	
	if not id in charaTags[group]:
		return False
	
	if not tag in charaTags[group][id]:
		return False
		
	return True
	
def getManualTags(group, id):
	charaTags = getCharacterTags()
	if not group in charaTags:
		return []
	if not id in charaTags[group]:
		return []
	
	tags = []
	for tag, is_set in charaTags[group][id].items():
		if is_set:
			tags.append(tag)
	return tags
	
def getManualTag(group, id, tag):
	if not hasManualTag(group, id, tag):
		return False
	
	charaTags = getCharacterTags()
	return charaTags[group][id][tag]
	
def setManualTag(group, id, tag, value):
	charaTags = getCharacterTags()
	
	if not group in charaTags:
		charaTags[group] = {}
	if not id in charaTags[group]:
		charaTags[group][id] = {}
	
	charaTags[group][id][tag] = value
	saveCharacterTags(charaTags)
	
def getMissingManualTags(group, tag, sort_tag=None, require=[], avoid=[]):
	allIds = getCropIds(group)
	
	ids = list(filter(lambda x: not hasManualTag(group, x, tag), allIds))
	
	for t in avoid:
		ids = list(filter(lambda x: not getManualTag(group, x, t), ids))
	
	for t in require:
		ids = list(filter(lambda x: getManualTag(group, x, t), ids))
	
	if sort_tag:
		ids = sorted(ids, key=lambda x: getTagStrength(group, x, sort_tag), reverse=True)
		
	return ids
	
	
def getAllManualTags(group):
	allIds = getCropIds(group)
	
	tags = set()
	for id in allIds:
		for tag in getManualTags(group, id):
			tags.add(tag)
	
	return list(tags)
	
	
def getTagStrength(group, id, tag):
	auto_tags = getAutoTags(group, id)
	return tagger.tagStrength(auto_tags, tag)
	

def getIgnoreTags():
	path = getJsonPath('ignore_tags.json')
	if os.path.exists(path):
		return readJson(path)
	return {}
	
def saveIgnoreTags(hypertags):
	path = getJsonPath('ignore_tags.json')
	with open(path, "w") as f:
		json.dump(hypertags, f, indent=2)
		
def setIgnoreTags(group, on_tag, ignore_tags):
	ignoreJson = getIgnoreTags()
	if not group in ignoreJson:
		ignoreJson[group] = {}
	
	ignoreJson[group][on_tag] = ignore_tags
	saveIgnoreTags(ignoreJson)
	
def getIgnoreTagsForTag(group, on_tag):
	ignoreJson = getIgnoreTags()
	if not group in ignoreJson:
		return []
	if not on_tag in ignoreJson[group]:
		return []
	return ignoreJson[group][on_tag]
	