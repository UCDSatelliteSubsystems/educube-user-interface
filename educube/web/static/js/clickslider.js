// NOTE: setup for these is done in commands.js

//$(document).ready(function() {
//    var slider = $("#spdslider")[0];
//    var text = $("#spdtxt")[0];
//    var range = {
//        'min': -100,
//        'max': 100
//    };
//
//    console.log("Creating ClickSlider");
//    console.log({slider : slider, text : text, range : range})
//    ClickSlider.create(slider, text, range);
//    console.log("Creating ClickSlider -- DONE");
//    
//    var slider = $("#exp_slider_1")[0];
//    var text = $("#exp_txt_1")[0];
//    var range = {
//        'min': 0,
//        'max': 100
//    };
//    
//    console.log("Creating ClickSlider");
//    console.log({slider : slider, text : text, range : range})
//    ClickSlider.create(slider, text, range);
//    console.log("Creating ClickSlider -- DONE");
//
//    var slider = $("#exp_slider_2")[0];
//    var text = $("#exp_txt_2")[0];
//    var range = {
//        'min': 0,
//        'max': 100
//    };
//    
//    console.log("Creating ClickSlider");
//    console.log({slider : slider, text : text, range : range})
//    ClickSlider.create(slider, text, range);
//    console.log("Creating ClickSlider -- DONE");
//});

function ClickSlider(slider, text, range, send_command) {
    _init(slider, text, range);
    function _init (slider, text, range) {
        noUiSlider.create(slider, {
            handles: 1,
    	    start:[0],
    	    step: 5,
    	    range: range,
    	    pips: { 
                 mode: 'count', 
                 values: 5 
                 }
            });
    
        slider.noUiSlider.on("set", on_set_slider_val(slider, text));
        slider.noUiSlider.on("slide", update_slider_text_val(text));
    
        var pips = slider.querySelectorAll('.noUi-value');
    
        for ( var i = 0; i < pips.length; i++ ) {
            // For this example. Do this in CSS! ???? HOW? ????
            pips[i].style.cursor = 'pointer';
            pips[i].addEventListener('click', click_on_pip(slider));
        }
    };

    function click_on_pip (slider) {
	var _click_on_pip = function() {
	    var value = Number($(this).data('value'));
	    slider.noUiSlider.set(value);
	};
	return _click_on_pip;
    };

    function on_set_slider_val (slider, text){
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
    };

    function update_slider_text_val (text){
	var _update_slider_text_val = function(speedval){
	    var speed = Math.round(speedval);
	    $(text).text(speed);
	};
	return _update_slider_text_val;
    };

};
