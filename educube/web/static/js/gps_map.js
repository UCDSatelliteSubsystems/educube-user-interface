

function MyMap (target) {
    var UCD = { lon : -6.2236, lat : 53.3083};

    this.zoomslider = new ol.control.ZoomSlider();

    this.map = new ol.Map({
        target: target,
        controls: ol.control.defaults({zoomslider: false}).extend([this.zoomslider]),
        layers: [
             new ol.layer.Tile({
           	     source: new ol.source.OSM()
                 }),
             ],
        view: new ol.View({
            center: ol.proj.fromLonLat([UCD.lon, 
                                        UCD.lat ]),
            zoom: 10,
            minZoom: 10,
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
