// Initialize map and title information
var mymap = L.map('mapid').setView([37.79, -122.2], 11);

L.tileLayer('https://api.tiles.mapbox.com/v4/{id}/{z}/{x}/{y}.png?access_token=pk.eyJ1IjoibWFwYm94IiwiYSI6ImNpejY4NXVycTA2emYycXBndHRqcmZ3N3gifQ.rJcFIG214AriISLbB6B5aw', {
	maxZoom: 18,
	attribution: 'Map data &copy; <a href="http://openstreetmap.org">OpenStreetMap</a> contributors, ' +
		'<a href="http://creativecommons.org/licenses/by-sa/2.0/">CC-BY-SA</a>, ' +
		'Imagery © <a href="http://mapbox.com">Mapbox</a>',
	id: 'mapbox.streets'
}).addTo(mymap);

// Functions for managing display of quantities
neighborhood_counts = {}
neighborhood_fines = {}
council_counts = {}
council_fines = {}
function process_data() {
	for (i=0; i<nc.length; i++) {
		neighborhood_counts[nc[i].neighborhood] = nc[i].count;
	}
	for (i=0; i<nf.length; i++) {
		neighborhood_fines[nf[i].neighborhood] = nf[i].fines;
	}
	for (i=0; i<cc.length; i++) {
		council_counts[cc[i].council] = cc[i].count;
	}
	for (i=0; i<cf.length; i++) {
		council_fines[cf[i].council] = cf[i].fines;
	}
}

map_objects = {}
function add_shapes(shape_class) {
	// Start off by removing whatever objects were already there
	for (m in map_objects) {
		map_objects[m].remove()
	}
	map_objects = {}
	// Decide which set of objects to use
	shapes = {"neighborhood":neighborhood_shapes, "council":council_shapes}[shape_class]
	counts = {"neighborhood":nc, "council":cc}[shape_class]
	fines = {"neighborhood":neighborhood_fines, "council":council_fines}[shape_class]
	// Add each individual shape with data
	years = ["12","13","14","15","16"];
	for (i=0; i<shapes.length; i++) {
		mod_shape = []
		// Latitude and longitude need to be switched.
		for (j=0; j < shapes[i].length; j++) {
			mod_shape = mod_shape.concat([[shapes[i][j][1], shapes[i][j][0]]])
		}
		message = "";
		if (shape_class == "neighborhood") {
			message = neighborhood_shapes_records[i][1];
		}
		if (shape_class == "council") {
			message = council_shapes_records[i][1];
		}
		// Shades of blue, with darker colors for more tickets.
		col = '#3388ff'
		if (i in counts) {
			if (counts[i]["count"] > 1000) {col = '#2266cc'}
			if (counts[i]["count"] > 10000) {col = '#2255aa'}
			if (counts[i]["count"] > 20000) {col = '#113377'}
			if (counts[i]["count"] > 30000) {col = '#000000'}
			message += "<br>" + counts[i]["count"].toString() + " tickets"
			for (y in years) {
				year = years[y];
				tickets_by_year = 0;
				if (year in counts[i]) {tickets_by_year = counts[i][year]}
				message += "<br>Tickets in 20" + year + ": " + tickets_by_year.toString();
			}
			if (i in fines) {
				average_fine = fines[i] / counts[i]["count"];
				message += "<br>Average fine of $" + Math.round(average_fine*100)/100;
			}
		}
		map_objects[i] = L.polygon(mod_shape,{color: col}).addTo(mymap).bindPopup(message);
		// Notice how we use the callbackClosure; this is so the map object "remembers" the parameter i.
		map_objects[i].on("click",callbackClosure( i, function(i) {
			if (i in counts) {
				document.getElementById("region").innerHTML = i;
				document.getElementById("count").innerHTML = counts[i]["count"];
			}
			else {
				document.getElementById("region").innerHTML = "???";
				document.getElementById("count").innerHTML = "???";
			}
		}));
	}
}

function callbackClosure(i, callback) {
	return function() { return callback(i);}
}

process_data();
add_shapes("neighborhood");
var popup = L.popup();