import { getMenu } from './api'
		

var menuContainer = document.getElementById("menu");
var itemsToAdd = await getMenu();

itemsToAdd.forEach(function(item){
	var li = document.createElement("li");
	
	var link = document.createElement("a");
	link.href = item['url'];
	link.innerHTML = item['text'];
	
	li.appendChild(link);
	menuContainer.appendChild(li);
});
