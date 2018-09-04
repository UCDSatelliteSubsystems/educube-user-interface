// call this in the html using <script> set_port({{port}}) </script> to 
// programatically set port? 
 var PORT = 0

function set_port(p){
    PORT = p
};

var websocket_addr = "ws://localhost:"+PORT+"/socket";

// creates a new websocket handler
// 
// Note: if additional msgtypes are added, then this will have to be extended!
// 
function setup_websocket(websocket_addr, telemetryhandler) {
    websocket = new WebSocket(websocket_addr);

    function _message_handler (event){
        console.log('Message received: ' event.data);
        _message = JSON.parse(event.data);
    
        if (_message.msgtype === 'telemetry'){
            telemetryhandler.handle_received_telemetry(_message.msgcontent);
        } else {
            console.log('WARNING: Unrecognised msgtype: ' _message.msgtype);
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

