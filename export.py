
from PIL import Image
import os
import os.path

import data
import tagger
import numpy as np


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
	prefix = ''
	upper_count = sum(1 for c in text if c.isupper())
	lower_count = sum(1 for c in text if c.islower())
	total = upper_count + lower_count
	if total != 0:
		if upper_count / total > 0.9:
			prefix = 'allcaps'
		elif lower_count / total > 0.9:
			prefix = 'lowercase'
		else:
			prefix = 'capitalized'
	
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
	
	return f'{prefix} "{text}"'
	
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
	remove_tags = ['sensitive', 'explicit', 'anime_coloring', 'general', 'parody', 'cosplay', 'virtual_youtuber', 'questionable', 'english_text', 'chinese_text']
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
		self.outFolderMask = 'out/' + sourceData + '_masks'
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
			
			if data.hasMask(id):
				if not os.path.exists(self.outFolderMask):
					os.makedirs(self.outFolderMask)
				base_value = 0.3
				mask = data.getMask(id).resize(cropped.size, Image.LANCZOS)
				arr = np.asarray(mask).astype(np.float32)
				rescaled_arr = np.clip(arr * (1.0 - base_value) + base_value * 255, 0, 255)
				mask = Image.fromarray(rescaled_arr.astype(np.uint8))
				
				mask.save(self.outFolderMask + '/' + id + '.png')
				
				
		
