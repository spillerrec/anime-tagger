export function getJSON(url, callback) {
	let xhr = new XMLHttpRequest();
	xhr.open('GET', url, true);
	xhr.responseType = 'json';
	xhr.onload = function() {
	let status = xhr.status;
	if (status === 200) {
		callback(null, xhr.response);
		} else {
			callback(status, xhr.response);
		}
	};
	xhr.send();
};

export async function getJson(url){
	const response = await fetch(url);
	return response.json()
}

export async function getJsonPost(url, request){
	const response = await fetch(url, {
		method: "POST",
		headers: {
			"Content-Type": "application/json"
		},
		body: JSON.stringify(request)
	});
	
	return response.json()
}

export async function getIds(tag){
	return await getJson(`/crops`);
	return await getJson(`/ids/${tag}`);
}

export async function getCustomTags(){
	return await getJson('/custom_tags');
}


export async function getHistogramForTag(tag){
	return await getJson('/get-tag-histo/' + tag);
}

export async function getSearch(tag){
	return await getJson(`/get-search/${tag}`);
}
