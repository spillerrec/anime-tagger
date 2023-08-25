
from PIL import Image
import json
import os
import os.path
wanted_tag = 'Amaama to Inazuma'
imagePath = wanted_tag
imagePathFull = 'images/' + imagePath
files = [os.path.join(imagePath, f) for f in os.listdir(imagePathFull) if os.path.isfile(os.path.join(imagePathFull, f))]
print(files)


def readJson(json_path, default_value):
	if os.path.exists(path):
		with open(json_path, encoding="utf-8") as json_file:
			return json.load(json_file)
	return default_value

def getAreas(path = 'area_tags.json'):
	return readJson(path, {})
	
def saveAreas(hypertags, path = 'area_tags.json'):
	with open(path, "w") as f:
		json.dump(hypertags, f, indent=2)
		
def getCharacterTags(path = 'character_tags.json'):
	return readJson(path, {})
		
areas = getAreas()
character_tags = getCharacterTags()


for id, rects in areas[wanted_tag].items():
	if len(rects) > 0:
		path = 'images/' + files[int(id)]
		rect = rects[0]
		img = Image.open(path)
		width, height = img.size
		x = max(0, int(rect['x']))
		y = max(0, int(rect['y']))
		w = int(rect['width'])
		h = int(rect['height'])
		w = min(width, x+w) - x
		h = min(height, y+h) - y
		
		if w > 0 and h > 0:
			print(path)
			print(rect)
			print(x, y, x + w, y + h)
			cropped = img.crop((x, y, x + w, y + h))
			cropped.save('out6/' + id + '.png')
		