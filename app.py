from flask import Flask, request, jsonify, send_file
import flask
from werkzeug.utils import secure_filename
import os
import os.path
import json
import sys
import io
from PIL import Image
import requests
import danbooru
import data
import tagger
from tqdm import tqdm


def hasTag(id, wanted_tag):
	(_, image_path, data) = common.getPostInfo(id)
	
	tags = data[0]['tags'].split(' ')
	
	include = []
	exclude = []
	for tag in wanted_tag.split(' '):
		if tag[0] == '-':
			exclude.append(tag[1:])
		else:
			include.append(tag)
	
	for wanted in include:
		if not wanted in tags:
			return False
	for disallowed in exclude:
		if disallowed in tags:
			return False
	
	#if wanted_tag in areas:
	#	if type in areas[wanted_tag]:
	#		if id in areas[wanted_tag][type]:
	#			return False
	return True

wanted_tag = sys.argv[1]
data.setSourceDir(wanted_tag)
files = data.getFiles(wanted_tag)
dan_files = danbooru.getFiles()
print(files)

app = Flask(__name__)

UPLOAD_FOLDER = 'images'
ALLOWED_EXTENSIONS = {'jpg', 'jpeg', 'png', 'gif'}
app.config['UPLOAD_FOLDER'] = '_assets'

def allowed_file(filename):
	return '.' in filename and \
		   filename.rsplit('.', 1)[1].lower() in ALLOWED_EXTENSIONS
		   
@app.route('/menuitems')
def serve_menuitems():
	return jsonify([
		{
			'text': 'Mark crops',
			'url': '/tag'
		},
		{
			'text': 'Automatic tagging',
			'url': '/autotag'
		},
		{
			'text': 'Manual tagging',
			'url': '/set_tag'
		},
		{
			'text': 'Tag filtering',
			'url': '/histogram'
		}
	])
			  

@app.route('/assets/<item>')
def serve_asset(item):
	f = app.config['UPLOAD_FOLDER']
	if os.path.exists(f + '/' + item + '.js'):
		item = item + '.js'
	
	return flask.send_from_directory(f, item)
	
@app.route('/')
def serve_main():
	return flask.send_from_directory(app.config['UPLOAD_FOLDER'], 'index.html')

@app.route('/tag')
def serve_tagger():
	return flask.send_from_directory(app.config['UPLOAD_FOLDER'], 'tag.html')

@app.route('/histogram')
def serve_histogram():
	return flask.send_from_directory(app.config['UPLOAD_FOLDER'], 'histogram.html')

@app.route('/download')
def serve_download():
	return flask.send_from_directory(app.config['UPLOAD_FOLDER'], 'download.html')

@app.route('/toggle_tags')
def serve_toggle():
	return flask.send_from_directory(app.config['UPLOAD_FOLDER'], 'add_tags.html')
	
	
@app.route('/set_tag')
def serve_set_tag():
	return flask.send_from_directory(app.config['UPLOAD_FOLDER'], 'set_category.html')

@app.route('/ids')
def serve_ids():
	return jsonify(data.getMissingIds(wanted_tag))

@app.route('/missingTagIds', methods=['POST'])
def serve_missing_tag_ids():
	tag = request.json['new_tag']
	sort = request.json['sort_by']
	require = request.json['require']
	exclude = request.json['exclude']
	if require:
		require = require.split(',')
	if exclude:
		exclude = exclude.split(',')
	return jsonify(data.getMissingManualTags(wanted_tag, tag, sort, require, exclude))
	
	
@app.route('/get-tag-histo/<in_tag>')
def serve_tag_histo(in_tag):	
	return jsonify(tagger.tagHistogram(wanted_tag, in_tag))
	
@app.route('/get-search/<in_tag>')
def serve_search(in_tag):
	cropIds = data.getCropIds(wanted_tag)

	items = []

	for id in cropIds:
		if data.getManualTag(wanted_tag, id, in_tag):
			items.append({'id': id, 'weight':1.0, 'checked':True})
		
		tagResult = 0.0
		if tagger.isValidTag(in_tag):
			tagResult = data.getTagStrength(wanted_tag, id, in_tag)
		
		items.append({'id':id, 'weight':tagResult, 'checked':tagResult > 0.35})
		
	res = sorted(items, key=lambda x:x['weight'])
	res.reverse()
	
	return jsonify(res)
	
	
@app.route('/set-tag', methods=['POST'])
def set_tag():
	print(request.json)
	
	extra = common.getExtra()
	tag = request.json['tag']
	setting = request.json['add']
	
	if not tag in extra:
		extra[tag] = {}
	
	for id in request.json['ids']:
		extra[tag][id] = setting
	
	common.saveExtra(extra)
	
	return '[true]'
	
@app.route('/set-category', methods=['POST'])
def set_category():
	res = request.json
	print(res)
	
	data.setManualTag(wanted_tag, res['id'], res['tag'], res['value'])
	
	return '[true]'
	
@app.route('/set-ignore-tags', methods=['POST'])
def set_ignore():
	res = request.json
	print(res)
	
	data.setIgnoreTags(wanted_tag, res['tag'], res['remove'])
	
	return '[true]'

def serve_pil_image(image):
	b = io.BytesIO()
	image.save(b, 'jpeg')
	b.seek(0)
	return send_file(
		b,
		mimetype="image/jpeg"
	)


def imageIdToPath(id):
	# Extract a crop index if it exists
	index = -1
	index_split = id.split('-')
	name = index_split[0]
	if len(index_split) == 2:
		index = int(index_split[1])
	
	# Figure out if we need to look at the danbooru images or the local ones
	components = name.split('_')
	if len(components) == 2:
		return (dan_files[name], index)
	else:
		return ('images/' + files[int(name)], index)

def loadImageFromId(id):
	image_path, index = imageIdToPath(id)
	
	if index >= 0:
		return data.getCroppedImage(wanted_tag, id)
	else:
		return data.asRgb(Image.open(image_path))
	

@app.route('/image/<id>')
def serve_file(id):
	return serve_pil_image(loadImageFromId(id))

@app.route('/image/<id>/<size>')
def serve_file_resized(id, size):
	s = int(size)
	image = loadImageFromId(id)
	image.thumbnail((s, s), Image.LANCZOS)
	return serve_pil_image(image)


@app.route('/add-tag', methods=['POST'])
def add_tag_area():
	print(request.json)
	
	areas = data.getAreas()
	
	areas[request.json['id']] = request.json['rects']
	
	data.saveAreas(areas)
	
	return '[true]'
	
@app.route('/custom_tags')
def get_custom_tags():
	return jsonify(data.getAllManualTags(wanted_tag))
	
@app.route('/autotag')
def autotag():
	cropIds = data.getCropIds(wanted_tag)
	
	for id in tqdm(cropIds):
		tagResult = data.getAutoTags(wanted_tag, id)
	data.writeTaggerCache()
	return 'done'


if __name__ == '__main__':
	app.run(host="localhost", port=8888)
