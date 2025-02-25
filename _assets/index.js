import { getSearch } from './api'
		
let ids = [];

let updatePage = function(){
	let resultsDiv = document.getElementById("imagelist");
	while (resultsDiv.firstChild) {
		resultsDiv.removeChild(resultsDiv.firstChild);
	}
	ids.forEach(function(item){
		var img = document.createElement("img");
		var id = item['id'];
		img.src = `/image/${id}/512`;
		resultsDiv.appendChild(img);
	});
};

async function update() {
	var inputValue = document.getElementById("searchbox").value;
	ids = await getSearch(inputValue);
	console.log(ids);
	updatePage();
}


document.getElementById('searchbox').addEventListener('input', update);
