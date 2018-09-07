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
        telemetryhandler = new TelemetryHandler();
        socket           = setup_websocket(websocket_address,
                                           telemetryhandler  );
        commandhandler   = new CommandHandler(socket);
    
        console.log('map');
        console.log($('#gps-map'));
	//        gps_map = new MyMap($('#gps-map'));
        gps_map = new MyMap('gps-map');
        console.log(gps_map.map);
        console.log('map -- DONE');

        console.log("EduCube JavaScript setup complete.");
    };
    _client_setup();
};

