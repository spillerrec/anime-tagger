import numpy
from PIL import Image
import onnxruntime as rt
import json

import data

tags = []
with open("workdir/model_tags.json", "r") as f:
	tags = json.load(f)
tag_categories = []
with open("workdir/tag_categories.json", "r") as f:
	tag_categories = json.load(f)
	
sess = rt.InferenceSession("model.onnx", providers=rt.get_available_providers())


def evaluate(image):
	
	im = image.resize((448, 448))
	
	arr = numpy.asarray(im)[...,[2,1,0]]
	input_name = sess.get_inputs()[0].name
	
	res = sess.run(None, {input_name: numpy.expand_dims(arr.astype(numpy.float32), 0)})
	return res[0][0]


def tag(index):
	return tags[index]

def category(index):
	if index >= len(tag_categories):
		return "other"
	return tag_categories[index]
	
	
def tagStrength(res, tag):
	index = tags.index(tag)
	return res[index]

def sortTags(res):
	
	original = res.copy()
	sorted = numpy.flip(numpy.argsort(res))
	for val in sorted:
	#for i, val in enumerate(res[0][0]):
		name = tags[val]
		#amount = val * 100
		amount = original[val] * 100
		#if amount < 15:
		#	break
		if amount > 15:
			print(f"{name}: {amount:.1f} %,")
			
			
def tagsAboveThreshold(res, threshold):
	
	original = res.copy()
	sorted = numpy.flip(numpy.argsort(res))
	
	items = []
	for val in sorted:
		if original[val] > threshold:
			items.append(tag(val))
	return items
	
def tagHistogram(wanted_tag, in_tag):
	cropIds = data.getCropIds(wanted_tag)
	ignores = data.getIgnoreTagsForTag(wanted_tag, in_tag)

	sum = None
	count = None

	for id in cropIds:
		if not data.getManualTag(wanted_tag, id, in_tag):
			continue
		
		tagResult = numpy.array(data.getAutoTags(wanted_tag, id))
		
		if sum is None:
			sum   = numpy.zeros(tagResult.shape)
			count = numpy.zeros(tagResult.shape)
		
		sum = sum + tagResult
		count = count + numpy.greater(tagResult, 0.35).astype(int)
		
	
	histogram = []
	for i in range(sum.shape[0]):
		histogram.append( {
			'tag' : tag(i),
			'sum' : sum[i],
			'count': count[i],
			'category': category(i),
			'checked': tag(i) in ignores 
		} )
		
	res = sorted(histogram, key=lambda x:x['sum'])
	res.reverse()
	
	grouped = {}
	for item in res:
		cat = item['category']
		if item['count'] > 0 or item['sum'] > 0.5:
			if cat in grouped:
				grouped[cat].append(item)
			else:
				grouped[cat] = [item]
	
	return grouped