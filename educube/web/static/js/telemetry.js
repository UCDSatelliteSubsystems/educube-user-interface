var websocket;
var websocket_addr="ws://localhost:18888/socket";

var notification_stack = {
    "dir1": "down", 
    "dir2": "right", 
    "push": "top",
};


$(document).ready(function () {
    setup_notifications();
    setup_websocket();
    parse_existing();
    setInterval(parse_existing, 5000);
});

function parse_existing(){
    parse_telemetry(telemetry_store['EPS']);
    parse_telemetry(telemetry_store['ADC']);
    parse_telemetry(telemetry_store['EXP']);
    parse_telemetry(telemetry_store['CDH']);
}

function setup_notifications(){
    PNotify.prototype.options.styling = "bootstrap3";
    PNotify.prototype.options.delay = 500;
}

function setup_websocket(){
    websocket = new WebSocket(websocket_addr);
    websocket.onmessage = function(event) {
       var telem_string = event.data;
       var telemetry = JSON.parse(telem_string);
       console.log("Received new telemetry from educube");
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

/*
######################################
# Telemetry parser
######################################
*/
var telemetry_store = {
};

telemetry_store = {"CDH":{"telem":"GPS,16/10/26T20:24:31,2595,7958,21226,-1114","data":{"GPS_FIX":{"LAT":"25.92335","LON":"79.51238"},"GPS_META":{"HDOP":"21226","ALT_CM":"-1114"},"GPS_DATE":"16/10/26T20:24:31"},"type":"T","board":"CDH","time":1477513190251.986},"EPS":{"telem":"I,66,1.67,6.58,17.00|I,67,11.84,4.95,118.20|I,73,-0.01,32.76,-0.10|I,68,6.20,4.95,62.40|I,69,5.30,4.95,53.10|I,72,-0.01,32.76,-0.10|I,70,2.22,4.96,22.30|I,74,-0.01,32.76,-0.10|I,71,0.06,4.96,0.20|I,75,-0.01,32.76,-0.10|I,65,0.01,6.62,0.20|I,64,-0.01,1.11,-0.10|DA,25.72,6.93,975.00|DB,191.69|DC,171.13|C,0","data":{"CHARGING":false,"DS18B20_B":{"temp":"171.13"},"INA":[{"bus_V":"6.58","current_mA":"17.00","shunt_V":"1.67","address":"66"},{"bus_V":"4.95","current_mA":"118.20","shunt_V":"11.84","address":"67"},{"bus_V":"32.76","current_mA":"-0.10","shunt_V":"-0.01","address":"73"},{"bus_V":"4.95","current_mA":"62.40","shunt_V":"6.20","address":"68"},{"bus_V":"4.95","current_mA":"53.10","shunt_V":"5.30","address":"69"},{"bus_V":"32.76","current_mA":"-0.10","shunt_V":"-0.01","address":"72"},{"bus_V":"4.96","current_mA":"22.30","shunt_V":"2.22","address":"70"},{"bus_V":"32.76","current_mA":"-0.10","shunt_V":"-0.01","address":"74"},{"bus_V":"4.96","current_mA":"0.20","shunt_V":"0.06","address":"71"},{"bus_V":"32.76","current_mA":"-0.10","shunt_V":"-0.01","address":"75"},{"bus_V":"6.62","current_mA":"0.20","shunt_V":"0.01","address":"65"},{"bus_V":"1.11","current_mA":"-0.10","shunt_V":"-0.01","address":"64"}],"DS2438":{"current":"975.00","voltage":"6.93","temp":"25.72"},"DS18B20_A":{"temp":"191.69"}},"type":"T","board":"EPS","time":1477513190254.175},"ADC":{"telem":"SOL,4,3,3,8|ANG,-90|MAG,1,1,1,1|WHL,3|MPU,ACC,-4.76,4.33,995.91|MPU,GYR,-0.21,-0.01,-0.08|MPU,MAG,-6057.53,-120.90,-2044.97","data":{"MPU_GYR":{"Y":"-0.01","X":"-0.21","Z":"-0.08"},"SUN_DIR":"-90","MPU_MAG":{"Y":"-120.90","X":"-6057.53","Z":"-2044.97"},"SUN_SENSORS":{"FRONT":"4","RIGHT":"8","BACK":"3","LEFT":"3"},"REACT_WHEEL":"-90","MPU_ACC":{"Y":"4.33","X":"-4.76","Z":"995.91"},"MAGNO_TORQ":{"X_P":"1","Y_P":"1","Y_N":"1","X_N":"1"}},"type":"T","board":"ADC","time":1477513190255.884},"EXP":{"telem":"THERM_P1,0|THERM_P2,0|I,64,-0.04,0.00,-0.80|I,67,-0.04,0.00,-0.10|P1A,18.50|P1B,18.50|P1C,18.44|P2A,18.56|","data":{"PANEL_TEMP":{"P2":{"A":"18.56"},"P1":{"A":"18.50","C":"18.44","B":"18.50"}},"THERM_PWR":{"P2":"0","P1":"0"},"INA":[{"bus_V":"0.00","current_mA":"-0.80","shunt_V":"-0.04","address":"64"},{"bus_V":"0.00","current_mA":"-0.10","shunt_V":"-0.04","address":"67"}]},"type":"T","board":"EXP","time":1477513190254.983}}

function parse_telemetry(telemetry){
    if (telemetry.type == "T"){
        console.log("Handling telemetry: " + telemetry.board);
        telemetry_store[telemetry.board] = telemetry;

        var telem_template;
        var telem_dom;
        if (telemetry.board == "EPS"){
            telem_template = "#tmpl-eps_telem_view"; telem_dom = "#board_eps .telem_content";
        }  
        if (telemetry.board == "ADC"){
            telem_template = "#tmpl-adc_telem_view"; telem_dom = "#board_adc .telem_content";
        }  
        if (telemetry.board == "EXP"){
            telem_template = "#tmpl-exp_telem_view"; telem_dom = "#board_exp .telem_content";
        }  
        if (telemetry.board == "CDH"){
            telem_template = "#tmpl-cdh_telem_view"; telem_dom = "#board_cdh .telem_content";
        }
        var telem_html = $(telem_template).tmpl(telemetry.data);
        $(telem_dom).html(telem_html);
        update_telem_indicators();
    }
}

function update_telem_indicators(){
    // ADC 
    var status_html = $('#tmpl-telem_status').tmpl({"telem":telemetry_store['ADC']});
    $('#telem_status_adc').html(status_html);
    // EXP 
    var status_html = $('#tmpl-telem_status').tmpl({"telem":telemetry_store['EXP']});
    $('#telem_status_exp').html(status_html);
    // CDH 
    var status_html = $('#tmpl-telem_status').tmpl({"telem":telemetry_store['CDH']});
    $('#telem_status_cdh').html(status_html);
    // EPS 
    var status_html = $('#tmpl-telem_status').tmpl({"telem":telemetry_store['EPS']});
    $('#telem_status_eps').html(status_html);
    
}