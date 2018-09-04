// call this in the html using <script> set_port({{port}}) </script> to 
// programatically set port? 
var PORT = 18888;

function set_port(p){
    PORT = p
};

//var websocket_addr = "ws://localhost:"+PORT+"/socket";
var websocket_addr = "ws://localhost:18888/socket";
// creates a new websocket handler
// 
// Note: if additional msgtypes are added, then this will have to be extended!
// 
//function setup_websocket(websocket_addr, telemetryhandler) {
function setup_websocket() {
    console.log(websocket_addr);
    websocket = new WebSocket(websocket_addr);

    function _message_handler (event){
        _message = JSON.parse(event.data);
	//        console.log('Message received: %o' _message);
        console.log('Message received: '+event.data);
    
        if (_message.msgtype === 'telemetry'){
            handle_received_telemetry(_message.msgcontent);
        } else {
            console.log('WARNING: Unrecognised msgtype: '+_message.msgtype);
        }
    };

    function _onopen() {
        console.log("websocket: open");
    };

    function _onclose() {
        console.log("websocket: closed");
    };

    websocket.onmessage = _message_handler;
    websocket.onopen = _on_open;
    websocket.onclose = _on_close;

    return websocket
};

function handle_received_telemetry(packet) {
    parse_telemetry(packet);
};