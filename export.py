
from PIL import Image
import os
import os.path

import data
import tagger

class Exporter:
	def __init__(self, sourceData):
		self.sourceData = sourceData
		
		self.batchLookup = data.getBatchLookup(sourceData)
		self.batchInfo = data.getBatchInfo()
		
		self.outFolder = 'out/' + sourceData
		if not os.path.exists(self.outFolder):
			os.makedirs(self.outFolder)
		self.remove_tags = ['sensitive', 'explicit', 'anime_coloring', 'general', 'parody', 'cosplay', 'virtual_youtuber', 'questionable']
		self.add_tags = []#['anime_screencap']
	
	def allIds(self):
		return data.getCropIds(self.sourceData)
	
	def export(self, id, replace_existing = False):
		outPath = self.outFolder + '/' + id
		outPathPng = outPath + '.png'
		already_exported = os.path.exists(outPathPng)
		
		
		cropped = data.getCroppedImage(self.sourceData, id)
		if cropped:
			batchTags = []
			batch = self.batchLookup[int(id.split('-')[0])]
			if batch in self.batchInfo:
				self.batchInfo[batch]['tags']
			tagResult = data.getAutoTags(self.sourceData, id)
			tags = tagger.tagsAboveThreshold(tagResult, 0.35)
			
			manual_tags = data.getManualTags(self.sourceData, id) + batchTags
			
			#if 'jiyuuga-saki-uniform' in manual_tags:
			#	manual_tags.remove('jiyuuga-saki-uniform')
			
			#Remove tags which should be ignored if a specific other tag exists
			for manual_tag in manual_tags:
				for ignore in data.getIgnoreTagsForTag(self.sourceData, manual_tag):
					if ignore in tags:
						tags.remove(ignore)
			
			#Remove disallowed tags
			for tag in self.remove_tags:
				if tag in tags:
					tags.remove(tag)
			
			#if 'thighhighs' in manual_tags:
			#	manual_tags.remove('thighhighs')
			tags = manual_tags + self.add_tags + tags
			
			
			with open(outPath + '.txt', 'w') as f:
				f.write(', '.join(tags).replace('_', ' '))
				
			if not already_exported or replace_existing:
				cropped.save(outPathPng)
		
