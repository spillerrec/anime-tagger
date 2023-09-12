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
import data
import tagger


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
files = data.getFiles(wanted_tag)
print(files)

app = Flask(__name__)

UPLOAD_FOLDER = 'images'
ALLOWED_EXTENSIONS = {'jpg', 'jpeg', 'png', 'gif'}
app.config['UPLOAD_FOLDER'] = '_assets'

def allowed_file(filename):
	return '.' in filename and \
		   filename.rsplit('.', 1)[1].lower() in ALLOWED_EXTENSIONS
			  

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
	
	
@app.route('/crops')
def serve_crops():
	return jsonify(data.getCropIds(wanted_tag))
	
@app.route('/get-tag-histo/<in_tag>')
def serve_tag_histo(in_tag):	
	return jsonify(tagger.tagHistogram(wanted_tag, in_tag))
	cropIds = data.getCropIds(wanted_tag)

	histogram = {}

	for id in cropIds:
		if not data.getManualTag(wanted_tag, id, in_tag):
			continue
		
		tagResult = data.getAutoTags(wanted_tag, id)
		tags = tagger.tagsAboveThreshold(tagResult, 0.35)
		
		for tag in tags:
			if not tag in histogram:
				histogram[tag] = 0
			histogram[tag] = 1 + histogram[tag]
		
	res = sorted(histogram.items(), key=lambda x:x[1])
	res.reverse()
	
	print(res)
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
	
@app.route('/thumbnail/<size>/<id>')
def serve_thumbnail(size, id):
	image_path = 'images/' + files[int(id)]
	s = int(size)
	print(image_path)
	path = image_path
	if os.path.exists(path):
		img = Image.open(path)
		img.thumbnail((s, s), Image.ANTIALIAS)
		
		b = io.BytesIO()
		img.save(b, 'png')
		b.seek(0)
		print(len(img.tobytes()))
		return send_file(
			b,#b,
			mimetype="image/png"
		)
	print('Warning, did not find: ' + image_path)
	return ''
	
@app.route('/crop/<id>')
def serve_crop(id):
	img = data.getCroppedImage(wanted_tag, id)
	
	b = io.BytesIO()
	img.save(b, 'jpeg')
	b.seek(0)
	print(len(img.tobytes()))
	return send_file(
		b,#b,
		mimetype="image/jpeg"
	)
	
@app.route('/images/<id>')
def serve_file(id):
	image_path = files[int(id)]
	print(image_path)
	img = Image.open('images/' + image_path)
	
	b = io.BytesIO()
	img.save(b, 'png')
	b.seek(0)
	print(len(img.tobytes()))
	return send_file(
		b,#b,
		mimetype="image/png"
	)
	return flask.send_from_directory('images/', image_path)


def readJson(json_path):
	with open(json_path, encoding="utf-8") as json_file:
		return json.load(json_file)

def readJsonIf(path, default_value={}):
	if os.path.exists(path):
		return readJson(path)
	return default_value
	
def getAreas(path = 'area_tags.json'):
	extra_tags = {}
	if os.path.exists(path):
		return readJson(path)
	return {}
	
def saveAreas(hypertags, path = 'area_tags.json'):
	with open(path, "w") as f:
		json.dump(hypertags, f, indent=2)
		
areas = getAreas()

@app.route('/add-tag', methods=['POST'])
def add_tag_area():
	print(request.json)
	
	if not wanted_tag in areas:
		areas[wanted_tag] = { }
	
	areas[wanted_tag][request.json['id']] = request.json['rects']
	
	saveAreas(areas)
	
	return '[true]'
	
@app.route('/custom_tags')
def get_custom_tags():
	return jsonify(data.getAllManualTags(wanted_tag))

if __name__ == '__main__':
	app.run(host="localhost", port=8888)
