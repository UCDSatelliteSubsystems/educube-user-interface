$(document).ready(function () {
    hook_command_feeders();
    hook_commands();
});

function hook_commands(){
    $('.educube_action').click(function(){
        var command = $(this).data("cmd");
        var board = $(this).data("board");
        var cmdstring = "C|" + board + "|" + command;

        try {
            websocket.send(cmdstring);
            provide_notice({"message": "Command sent ("+cmdstring+")", "type": "success"});
        }
        catch(err) {
            console.log(err);
            provide_notice({"message": "Command failed", "type": "error"});
        }
    });
}


function hook_command_feeders(){
    $('.feed_educube_action').change(function() {
        var dest_selector = $(this).data("actionsel");
        var cmd_val = $(this).val();
        if ($(this).hasClass("feed_switch_sign_before")){
            if (parseInt(cmd_val) > 0)
                cmd_val = "+|" + cmd_val;
            else
                cmd_val = "-|" + Math.abs(cmd_val);
        }
        var cmd_feed = $(this).data("cmdbefore") + cmd_val + $(this).data("cmdafter");
        $(dest_selector).data("cmd", cmd_feed);
    });
}

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