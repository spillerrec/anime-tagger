
from PIL import Image
import json
import os
import os.path

import data
import sys

sourceData = sys.argv[1]


data = data.readJson(sourceData)

for name in data:
	print(name)
	
	outPath = 'images/' + name + '/' + sourceData
	with open(outPath, "w") as f:
		json.dump(data[name], f, indent=2)