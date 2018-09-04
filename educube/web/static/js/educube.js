



$(document).ready(function(){





        telemetryhandler = setup_telemetryhandler();
	websocket = setup_websocket(websocket_addr, );


	// actually -- if we pass websocket as an argument to the send_command
	// function, then we don't need to have websocket at a global
	// namespace. This means that there is no need to instantiate
	// commandhandler after websocket???
        commandhandler = setup_commandhandler(websocket);

        console.log("JavaScript setup complete.");
    });


