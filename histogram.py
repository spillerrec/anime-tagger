
from PIL import Image
import json
import os
import os.path

import data
import tagger

sourceData = 'Amaama to Inazuma'
wanted_tag = 'kotori'

cropIds = data.getCropIds(sourceData)

histogram = {}

for id in cropIds:
	if not data.getManualTag(sourceData, id, wanted_tag):
		continue
		
	tagResult = data.getAutoTags(sourceData, id)
	tags = tagger.tagsAboveThreshold(tagResult, 0.35)
	
	for tag in tags:
		if not tag in histogram:
			histogram[tag] = 0
		histogram[tag] = 1 + histogram[tag]
	
res = sorted(histogram.items(), key=lambda x:x[1])
res.reverse()
print(res)