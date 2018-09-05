//$(document).ready(client_setup(port));

/* client_setup
/* 
/* 
/****/
function client_setup(port) {
    var websocket_address = "ws://localhost:"+port+"/socket";

    function _client_setup(){
	console.log("EduCube JavaScript setup");
    
        // this smells... I don't like that these components are so
        // interdependent that they have to be set up in a particular order!
        telemetryhandler = setup_telemetryhandler();
    	websocket = setup_websocket(websocket_addr, telemetryhandler);
    
    
    	// actually -- if we pass websocket as an argument to the send_command
    	// function, then we don't need to have websocket at a global
    	// namespace. This means that there is no need to instantiate
    	// commandhandler after websocket???
        commandhandler = setup_commandhandler(websocket);

        console.log("EduCube JavaScript setup complete.");
    };
    return _client_setup
};

