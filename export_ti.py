
from PIL import Image
import json
import os
import os.path
from tqdm import tqdm

import data
import tagger
import sys

sourceData = sys.argv[1]
targetTagName = sys.argv[2]
outputTagName = sys.argv[3]
data.setSourceDir(sourceData)
remove_tags = ['sensitive', 'explicit', 'anime_coloring', 'general', 'parody', 'cosplay', 'virtual_youtuber', 'questionable']
add_tags = []#['anime_screencap']
replace_existing = False

cropIds = data.getCropIds(sourceData)

outFolder = 'out/' + sourceData + '_' + outputTagName
if not os.path.exists(outFolder):
	os.makedirs(outFolder)
	
batchLookup = data.getBatchLookup(sourceData)
batchInfo = data.getBatchInfo()

for id in tqdm(cropIds):
	outPath = outFolder + '/' + id
	outPathPng = outPath + '.png'
	already_exported = os.path.exists(outPathPng)
	
	
	cropped = data.getCroppedImage(sourceData, id)
	if cropped:
		batchTags = batchInfo[batchLookup[int(id.split('-')[0])]]['tags']
		tagResult = data.getAutoTags(sourceData, id)
		tags = tagger.tagsAboveThreshold(tagResult, 0.35)
		
		manual_tags = data.getManualTags(sourceData, id) + batchTags
		if not targetTagName in manual_tags:
			continue
		manual_tags = [outputTagName]
		
		#Remove tags which should be ignored if a specific other tag exists
		for ignore in data.getIgnoreTagsForTag(sourceData, targetTagName):
			if ignore in tags:
				tags.remove(ignore)
		
		#Remove disallowed tags
		for tag in remove_tags:
			if tag in tags:
				tags.remove(tag)
		
		tags = manual_tags + add_tags + tags
		
		
		with open(outPath + '.txt', 'w') as f:
			f.write(', '.join(tags).replace('_', ' '))
			
		if not already_exported or replace_existing:
			cropped.save(outPathPng)
			
data.writeTaggerCache()
