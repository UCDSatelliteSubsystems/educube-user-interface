// call this in the html using <script> set_port({{port}}) </script> to 
// programatically set port? 
//
//function set_port(p){
//    PORT = p
//};
//
//var websocket_addr = "ws://localhost:"+PORT+"/socket";
// creates a new websocket handler
// 
// Note: if additional msgtypes are added, then this will have to be extended!
// 

function setup_websocket(websocket_address, telemetryhandler) {
    console.log("websocket_address : "+websocket_address);
    websocket = new WebSocket(websocket_address);

    function _message_handler (event){
        _message = JSON.parse(event.data);
	//        console.log('Message received: %o' _message);
        console.log('Message received: '+event.data);
    
        if (_message.msgtype === 'telemetry'){
            telemetryhandler.handle_received_telemetry(_message.msgcontent);
        } else {
            console.log('WARNING: Unrecognised msgtype: '+_message.msgtype);
        }
    };

    function _on_open() {
        console.log("websocket: open");
    };

    function _on_close() {
        console.log("websocket: closed");
	// alerts the user that EduCube is no longer connected.
	// TODO: tidy up the web interface?
        // TODO: replace system alert box with custom formatted box? 
	alert("The websocket connection was closed by the server");
    };

    websocket.onmessage = _message_handler;
    websocket.onopen = _on_open;
    websocket.onclose = _on_close;

    return websocket
};

//function handle_received_telemetry(packet) {
//    parse_telemetry(packet);
//};