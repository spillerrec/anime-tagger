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
#import danbooru
import data
import tagger
from export import Exporter
from tqdm import tqdm
import threading


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
dan_files = []#danbooru.getFiles()
print(files)

progress_bars = {}

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
		},
		{
			'text': 'Export images',
			'url': '/export'
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
	
@app.route('/set_text')
def serve_set_text():
	return flask.send_from_directory(app.config['UPLOAD_FOLDER'], 'set_text.html')
	
@app.route('/set_pose')
def serve_set_pose():
	return flask.send_from_directory(app.config['UPLOAD_FOLDER'], 'set_pose.html')
	
@app.route('/set_mask')
def serve_set_mask():
	return flask.send_from_directory(app.config['UPLOAD_FOLDER'], 'set_mask.html')

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
	
@app.route('/missingTextIds')
def serve_missing_text_ids():
	return jsonify(data.getMissingTextIds())
	
@app.route('/missingMaskIds')
def serve_missing_mask_ids():
	return jsonify(data.getMissingMaskIds())
	
	
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
	
@app.route('/set-text', methods=['POST'])
def set_text():
	res = request.json
	print(res)
	
	data.setText(res['id'], res['text'])
	
@app.route('/set-pose', methods=['POST'])
def set_pose():
	res = request.json
	print(res)
	
	data.setPose(res['id'], res['pose'])
	
	return '[true]'
	
@app.route('/set-mask/<id>', methods=['POST'])
def set_mask(id):
	print(request.files)
	file = request.files['image']
	if file.filename == '':
		return '[false]'
		
	try:
		image = Image.open(file.stream)
		data.setMask(id, image)
	except Exception as e:
		return '[false]'
	
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

@app.route('/view/image/<id>')
def view_image(id):
	return flask.send_from_directory(app.config['UPLOAD_FOLDER'], 'view_image.html')

def flatten(nested):
	return [item for sublist in nested for item in sublist]

@app.route('/data/image/<id>')
def data_image(id):
	from export import BatchInfo, calculateTagString
	tagList = tagger.tagList()
	tagStrength = data.getAutoTags(wanted_tag, id)
	
	batchInfo = BatchInfo(wanted_tag)
	batch = batchInfo.getBatchFromCropId(id)
	batchTags = batch['tags'] if batch is not None else []
	
	active_tags = tagger.tagsAboveThreshold(tagStrength, 0.35)
	
	manual_tags = data.getManualTags(wanted_tag, id)
	ignore_tags = flatten([data.getIgnoreTagsForTag(wanted_tag, tag) for tag in manual_tags])
	
	text_strings = data.getText(id)
	
	prompt = calculateTagString(wanted_tag, active_tags, manual_tags, text_strings, batchTags)
	
	tags = [{
		'tag': tag,
		'strength': strength,
		'enabled': strength > 0.35 and not tag in ignore_tags
	} for tag, strength in zip(tagList, tagStrength)]
	tags = sorted(tags, key=lambda x: x['strength'], reverse=True)[:100]
	
	return jsonify({
		'manual_tags': manual_tags,
		'auto_tags': tags,
		'ignore_tags': ignore_tags,
		'prompt': prompt
	})


@app.route('/data/taglist')
def data_taglist():
	return jsonify(tagger.tagList())

@app.route('/data/autotags/<id>')
def data_autotags(id):
	return jsonify(data.getAutoTags(wanted_tag, id))

@app.route('/data/pose/<id>')
def data_pose(id):
	return jsonify(data.getPose(wanted_tag, id))

@app.route('/data/pose/missing')
def serve_missing_pose_ids():
	return jsonify(data.getMissingPoseIds())




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
	
def runAutotag():
	cropIds = data.getCropIds(wanted_tag)
	
	progress = tqdm(cropIds)
	progress_bars['autotag'] = progress.format_dict
	for id in progress:
		progress_bars['autotag'] = progress.format_dict
		tagResult = data.getAutoTags(wanted_tag, id)
	data.writeTaggerCache()
	progress_bars['autotag'] = progress.format_dict
	

@app.route('/autotag')
def autotag():
	thread = threading.Thread(target=runAutotag)
	thread.start()
	return flask.send_from_directory(app.config['UPLOAD_FOLDER'], 'autotag.html')
	
def runExport():
	exporter = Exporter(wanted_tag)
	cropIds = exporter.allIds()

	progress = tqdm(cropIds)
	progress_bars['export'] = progress.format_dict
	for id in progress:
		exporter.export(id)
		progress_bars['export'] = progress.format_dict
				
	data.writeTaggerCache()
	progress_bars['export'] = progress.format_dict

@app.route('/export')
def export():
	thread = threading.Thread(target=runExport)
	thread.start()
	return flask.send_from_directory(app.config['UPLOAD_FOLDER'], 'export.html')
	

@app.route('/progress/<bar>')
def progress(bar):
	return jsonify(progress_bars[bar])

if __name__ == '__main__':
	app.run(host="localhost", port=8888)
