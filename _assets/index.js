import { getIds } from './api'
		
let ids = [];

let updatePage = function(){
	let resultsDiv = document.getElementById("imagelist");
	while (resultsDiv.firstChild) {
		resultsDiv.removeChild(resultsDiv.firstChild);
	}
	ids.forEach(function(id){
		var img = document.createElement("img");
		//img.src = '/thumbnail/256/' + id['id'];
		img.src = '/crop/' + id;//id['id'];
		//img.title = id['prompt'];
		resultsDiv.appendChild(img);
	});
};

async function update() {
	var inputValue = document.getElementById("searchbox").value;
	ids = await getIds(inputValue);
	console.log(ids);
	updatePage();
}


document.getElementById('searchbox').addEventListener('input', update);
