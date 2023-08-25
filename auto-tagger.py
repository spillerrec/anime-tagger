import numpy
from PIL import Image
import onnxruntime as rt
import json

sess = rt.InferenceSession("model.onnx", providers=rt.get_available_providers())

tags = []
with open("model_tags.json", "r") as f:
	tags = json.load(f)

with Image.open("test.jpg") as im:
	arr = numpy.asarray(im)
	input_name = sess.get_inputs()[0].name
	#arr = arr / 255.0
	#arr = arr[...,[2,0,1]].copy()
	#print(arr)
	print(numpy.expand_dims(arr, 0).shape)
	res = sess.run(None, {input_name: numpy.expand_dims(arr.astype(numpy.float32), 0)})
	#print(numpy.argmax(res[0]))
	original = res[0][0].copy()
	sorted = numpy.flip(numpy.argsort(res[0][0]))
	for val in sorted:
	#for i, val in enumerate(res[0][0]):
		name = tags[val]
		#amount = val * 100
		amount = original[val] * 100
		#if amount < 15:
		#	break
		if amount > 15:
			print(f"{name}: {amount:.1f} %,")
		
	print(res[0][0][0:5])

