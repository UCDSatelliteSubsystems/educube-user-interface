//$(document).ready(client_setup(port));

/* client_setup
/* 
/* 
/****/
function EduCubeClientSocket(port) {
    var websocket_address = "ws://localhost:"+port+"/socket";

    function _client_setup(){
	console.log("EduCube JavaScript setup");
    
        // this smells... I don't like that these components are so
        // interdependent that they have to be set up in a particular order!

	// there is a bug here in how OpenLayers and Bootstrap work together,
	// which means that the map doesn't appear until the window is
	// resized. 
        console.log('Creating GPSMap');
        gps_map = new GPSMap('gps-map');
	//        gps_map.updateSize();
        console.log('Creating GPSMap -- DONE');

        telemetryhandler = new TelemetryHandler(gps_map);
        socket           = setup_websocket(websocket_address,
                                           telemetryhandler  );
        commandhandler   = new CommandHandler(socket);
    

        console.log("EduCube JavaScript setup complete.");
    };
    _client_setup();
};

