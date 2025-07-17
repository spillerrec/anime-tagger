
from PIL import Image
import os
import os.path

import data
import tagger


class BatchInfo:
	def __init__(self, sourceData):
		self.batchLookup = data.getBatchLookup(sourceData)
		self.batchInfo = data.getBatchInfo()
		
	def getBatchFromCropId(self, cropId):
		imageId = int(cropId.split('-')[0])
		if not imageId in self.batchLookup:
			return None
		
		batch = self.batchLookup[imageId]
		if not batch in self.batchInfo:
			return None
		
		return self.batchInfo[batch]
		
		
def flatten(nested):
	return [item for sublist in nested for item in sublist]
	
def transform_text_strings(text):
	text = text.lower()
	text = text.replace(' ', '_')
	text = ''.join(flatten(' '.join(text)))
	text = text.replace('\n', '|')
	#text = text.replace('♥', 'heart') # Lets leave them for now, it seems like they do have tolkens
	#text = text.replace('★', 'star')
	#text = text.replace('☆', 'star')
	text = text.replace(',', 'comma')
	text = text.replace('è', 'e') # Not sure about what to do with these
	# ~ remains '~' for now
	
	return f'text "{text}"'
	
def calculateTagString(sourceData, tags, manual_tags, text_strings, batchTags=[]):
	manual_tags = manual_tags + batchTags
	
	#if 'jiyuuga-saki-uniform' in manual_tags:
	#	manual_tags.remove('jiyuuga-saki-uniform')
	
	#Remove tags which should be ignored if a specific other tag exists
	for manual_tag in manual_tags:
		for ignore in data.getIgnoreTagsForTag(sourceData, manual_tag):
			if ignore in tags:
				tags.remove(ignore)
	
	#Remove disallowed tags
	remove_tags = ['sensitive', 'explicit', 'anime_coloring', 'general', 'parody', 'cosplay', 'virtual_youtuber', 'questionable']
	for tag in remove_tags:
		if tag in tags:
			tags.remove(tag)
	
	#if 'thighhighs' in manual_tags:
	#	manual_tags.remove('thighhighs')
	tags = manual_tags + tags
	
	text = ""
	if len(text_strings) > 0:
		for line in text_strings:
			text = text + transform_text_strings(line) + ", "
	
	return text + ', '.join(tags).replace('_', ' ')

class Exporter:
	def __init__(self, sourceData):
		self.sourceData = sourceData
		
		self.batchInfo = BatchInfo(sourceData)
		
		self.outFolder = 'out/' + sourceData
		if not os.path.exists(self.outFolder):
			os.makedirs(self.outFolder)
	
	def allIds(self):
		return data.getCropIds(self.sourceData)
	
	def export(self, id, replace_existing = False):
		outPath = self.outFolder + '/' + id
		outPathPng = outPath + '.png'
		already_exported = os.path.exists(outPathPng)
		
		
		cropped = data.getCroppedImage(self.sourceData, id)
		if cropped:
			batch = self.batchInfo.getBatchFromCropId(id)
			batchTags = batch['tags'] if batch is not None else []
			
			tagResult = data.getAutoTags(self.sourceData, id)
			tags = tagger.tagsAboveThreshold(tagResult, 0.35)
			
			manual_tags = data.getManualTags(self.sourceData, id)
			
			text_strings = data.getText(id)
			
			prompt = calculateTagString(self.sourceData, tags, manual_tags, text_strings, batchTags)
			with open(outPath + '.txt', 'w', encoding="utf-8") as f:
				f.write(prompt)
				
			if not already_exported or replace_existing:
				cropped.save(outPathPng)
		
