var UCD = { lon : -6.2236, lat : 53.3083};

/* GPSMap
/* 
/* 
/* 
/**/
function GPSMap (target) {
    var _markers = [];

    var _markerstyle = new ol.style.Style({
            image : new ol.style.Circle({
                    radius : 7,
                    fill : new ol.style.Fill({color : 'black'}),
                    stroke : new ol.style.Stroke({
                            color : 'white', width : 2
                        })
                })
        });

    var _vectorsource = new ol.source.Vector({
            features: _markers,
        });

    var _vectorlayer = new ol.layer.Vector({
            source : _vectorsource,
            style : _markerstyle,
        });

    this.add_marker = function add_marker(lon, lat) {
        var _geometry = new ol.geom.Point(
            ol.proj.transform([lon, lat],'EPSG:4326', 'EPSG:3857'));
        var _new_marker = new ol.Feature({
                geometry : _geometry,
            });
        _markers.push(_new_marker);
        // update markers on map
        _vectorsource.clear();
        _vectorsource.addFeatures(_markers);
    };

    this.update_marker = function update_marker(idx, lon, lat) {
        var _new_geometry = new ol.geom.Point(
            ol.proj.transform([lon, lat],'EPSG:4326', 'EPSG:3857'));
        _markers[idx].setGeometry(_new_geometry);
    };

    var _zoomslider = new ol.control.ZoomSlider();
    var _controls = ol.control.defaults({zoomslider: false});
    _controls.extend([_zoomslider]);

    this.map = new ol.Map({
	    target: target,
	    controls: _controls,
	    layers: [
		     new ol.layer.Tile({
			     source: new ol.source.OSM()
			 }),
             _vectorlayer
		     ],
	    view: new ol.View({
		    center: ol.proj.fromLonLat([UCD.lon, 
						UCD.lat ]),
		    zoom: 10,
		    minZoom: 11,
		    maxZoom: 17,
		}),
        });
};


//    function _init () { 
//        console.log("creating map");
//
////        var features = new ol.Feature({
////		geometry: new ol.geom.Point(
////                    ol.proj.fromLonLat([this.UCD.lon, this.UCD.lat])),
////                name: "EduCube",
////	    });
////
////        var markers = new ol.layer.Vector({
////		source: new ol.source.Vector({
////			features: features,
////		    })
////	    });
//
//
//        console.log(this.map);
//        console.log("map created");
