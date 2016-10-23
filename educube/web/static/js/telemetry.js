var websocket;
var notification_stack = {
    "dir1": "down", 
    "dir2": "right", 
    "push": "top",
    "context": $("#telemetry_block")
};


$(document).ready(function () {
    setup_notifications();
    setup_websocket();
});

function setup_notifications(){
    PNotify.prototype.options.styling = "bootstrap3";
    PNotify.prototype.options.delay = 500;
}

function setup_websocket(){
    websocket = new WebSocket("ws://localhost:8000/socket");
    websocket.onmessage = function(event) {
       var telem_string = event.data;
       var telemetry = JSON.parse(telem_string);
       console.log(telemetry);
       show_telemetry(telemetry);
       parse_telemetry(telemetry);
    }
}

function show_telemetry(telemetry) {
    new PNotify({
        text: "[" + telemetry.board + "] ("+ telemetry.type +") " + telemetry.telem,
        context: $("#telemetry_block"),
        stack: notification_stack,
        animate: {
            animate: true,
            animate_speed: 'fast',
            in_class: "bounceInRight",
            out_class: "fadeOutDown",
        }
    });
}

function parse_telemetry(telemetry){
    if (telemetry.type == "T"){
        if (telemetry.board == "EPS"){
            handle_board_telemetry_eps(telemetry.telem);
        }    
    }
}

function handle_board_telemetry_eps(eps_telem){
    var eps_html = $("#eps_telem_template").tmpl(eps_telem);
    $("#board_eps").html(eps_html);
}
