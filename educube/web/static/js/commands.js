$(document).ready(function () {
    hook_commands();
});

/* send_command
 *
 */
function send_command(command, board, settings){
    var cmd_packet = {
        msgtype    : 'command',
        msgcontent : {
            command  : command,
            board    : board,
            settings : settings,
	    }
	};

    try {
        console.log(cmd_packet);
        var cmd_string = JSON.stringify(cmd_packet);
	websocket.send(cmd_string);
        provide_notice({
            "message" : "Command sent ("+cmd_string+")", 
            "type"    : "success"
        });
    }
    catch(err) {
        console.log(err);
        provide_notice({"message": "Command failed", "type": "error"});
    }
}

/* hook_commands
 *
 */ 
function hook_commands(){
    $(document).on('click', '.educube_action', function(){
        var command  = $(this).data("cmd");
        var board    = $(this).data("board");
        var settings = $(this).data("settings");

        send_command(command, board, settings);
    });
}

//////////////////////////////////////////////////////////////////////////////
// 
// 
// 
// 
//////////////////////////////////////////////////////////////////////////////

// CAN WE REMOVE THIS CALL????? IT SHOULD BE REPLACED WITH A SPECIFIED CLASS
// FOR EACH SLIDER/TEXT, AND WITH A NEW RANGE ATTRIBUTE????
$(document).ready(function(){
    var slider = $("#spdslider")[0];
    var text = $("#spdtxt")[0];
    var range = {
        'min': -100,
        'max':  100
    };
    
    create_click_slider(slider, text, range);
    
    var slider = $("#exp_slider_1")[0];
    var text = $("#exp_pwr_txt_1")[0];
    var range = {
        'min': 0,
        'max': 100
    };
    
    create_click_slider(slider, text, range);
    
    var slider = $("#exp_slider_2")[0];
    var text = $("#exp_pwr_txt_2")[0];
    var range = {
        'min': 0,
        'max': 100
    };
    
    create_click_slider(slider, text, range);

    });



function create_click_slider (slider, text, range) {
    noUiSlider.create(slider, {
	    handles: 1,
		start:[0],
		step: 5,
		range: range,
		pips: { mode: 'count', values: 5 }
        });

    slider.noUiSlider.on("set", on_set_slider_val(slider, text));
    slider.noUiSlider.on("slide", update_slider_text_val(text));

    var pips = slider.querySelectorAll('.noUi-value');

    for ( var i = 0; i < pips.length; i++ ) {
        // For this example. Do this in CSS! ???? HOW? ????
        pips[i].style.cursor = 'pointer';
        pips[i].addEventListener('click', click_on_pip(slider));
    }
}

/* clickOnPip
 * closure returning function that responds to click on pip
 **/
function click_on_pip(slider) {
    var _click_on_pip = function() {
        var value = Number($(this).data('value'));
        slider.noUiSlider.set(value);
    };
    return _click_on_pip;
}

/* on_set_slider_val
 * Two things happen: 1) sets the text value to the highlighted slider value;
 * and 2) sends the value as a telemetry command
 **/
function on_set_slider_val(slider, text){
    var command  = $(slider).data('cmd');
    var board    = $(slider).data('board');
    var settings = $(slider).data('settings') || {};

    var _send_slider_val = function(speedval) {
        settings.val = Math.round(speedval);
        send_command(command, board, settings);
    };

    var _update_slider_text_val = update_slider_text_val(text);

    var _on_set_slider_val = function(speedval) {
        _update_slider_text_val(speedval);
        _send_slider_val(speedval);
    };
    return _on_set_slider_val;
}

/* update_slider_text_val
 * Closure that returns a function to be called to update an accompanying text
 * reader for a noUiSlider
 **/
function update_slider_text_val(text){
    var _update_slider_text_val = function(speedval){
        var speed = Math.round(speedval);
        $(text).text(speed);
    };
    return _update_slider_text_val;
}


//////////////////////////////////////////////////////////////////////////////
// provide_notice
// 
// 
//////////////////////////////////////////////////////////////////////////////
function provide_notice(msg) {
    text = msg.message;
    title = msg.title || false;
    icon = msg.icon || false;
    delay = 1500;
    // level parsing
    type = msg.type || "notice";
    // Check Desktop
    desktop = msg.desktop;
    if (desktop) PNotify.desktop.permission();
    return new PNotify({
        title: title,
        text: text,
        icon: icon,
        type: type,
        delay: delay,
        styling: "bootstrap3",
        desktop: {
            desktop: desktop
        }
    });
}