import { getCustomTags, getHistogramForTag } from './api'

let ids = [];

var updatePage = function(){
	let searchItem = document.getElementById("search_dropdown").value;
	var resultsDiv = document.getElementById("results");
	while (resultsDiv.firstChild) {
		resultsDiv.removeChild(resultsDiv.firstChild);
	}
	for (let category in ids) {
		var container = document.createElement("div");
		container.id = category;
		resultsDiv.append(container);
		
		var catName = document.createElement("h2");
		catName.innerHTML = category;
		container.append(catName);
		
		var tagList = document.createElement("div");
		tagList.classList.add("tag_list");
		container.append(tagList);
		
		ids[category].forEach(function(id){
			var count = document.createElement("p");
			count.classList.add("count");
			count.innerHTML = id.count;
			tagList.appendChild(count);
			
			
			var div2 = document.createElement("div");
			div2.classList.add("name");
			tagList.appendChild(div2);
			
			var name = document.createElement("input");
			name.type = "checkbox"
			name.id = id.tag;
			
			name.checked = id.checked;
			div2.appendChild(name);
			
			var nameLabel = document.createElement("label");
			nameLabel.for = id.tag;
			nameLabel.innerHTML = id.tag.replace('_', ' ');
			div2.appendChild(nameLabel);
			
			div2.addEventListener('click', function(event){
				event.preventDefault();
				if (event.altKey)
					window.open('/list/' + searchItem + '/' + id.tag + '/', '_blank').focus();
				else
					name.checked ^= 1;
			} );
			name.addEventListener('click', function(event){
				event.stopPropagation();
			} );
		});
	
	}
};

async function update() {
	let inputValue = document.getElementById("search_dropdown").value;
	ids = await getHistogramForTag( inputValue );
	updatePage();
}

async function updateCustomTags() {
	let select = document.getElementById("search_dropdown");
	while( select.firstChild )
		select.removeChild( select.firstChild );
	
	for( let tag of await getCustomTags() ){
		var item = document.createElement("option");
		item.value = tag;
		item.innerHTML = tag.replace('_', ' ');
		select.append( item );
	}
	update();
}

updateCustomTags();

function updateHyperTags(){
	let resultsDiv = document.getElementById("results");
	let entries = resultsDiv.getElementsByTagName("input");
	let items = [];
	for( let input of entries ){
		if (input.checked)
			items.push(input.id);
	}
	
	let updateEntry = {
		'tag' : document.getElementById("search_dropdown").value,
		'remove' : items
	};
	console.log(updateEntry);
	
	fetch("/set-ignore-tags", {
		method: "POST",
		headers: {
			"Content-Type": "application/json"
		},
		body: JSON.stringify(updateEntry)
	})
		.then(response => response.json())
		.then(data => console.log(data))
		.catch(error => console.error(error));
}

document.getElementById('updatehyper').addEventListener('click', updateHyperTags);
document.getElementById('search_dropdown').addEventListener('input', update);