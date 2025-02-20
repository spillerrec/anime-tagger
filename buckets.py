
buckets = [
	(256, 832),
	(320, 704),
	(384, 640),
	(448, 576),
	(512, 512),
	(576, 448),
	(640, 384),
	(704, 320),
	(768, 320)
]

def aspect(dims):
	(w, h) = dims
	return w / h
	
def closetBucket(dims):
	wanted = aspect(dims)
	
	allAspects = [abs(aspect(x) - wanted) for x in buckets]
	index = allAspects.index(min(allAspects))
	return buckets[index]
