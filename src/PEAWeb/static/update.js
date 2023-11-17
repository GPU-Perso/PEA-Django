// Stock Ajax update
var update = function(link) {
    if(event)
        event.preventDefault();
    var id = $(link).attr('id');
    var url = "/update/code/"+id;
    console.log(url);
    $("#row-"+id).load(url);
}

$(document).ready(function() {
    // Automatic Ajax updates every 2-4 minutes
    $(".update").each(function(i){
        var interval = 0;
        if($(this).hasClass('etf'))
            interval =  (Math.random()*(window.etf_interval_max - window.etf_interval_min) + window.etf_interval_min)*1000;
        else
            interval = (Math.random()*(window.stock_interval_max - window.stock_interval_min) + window.stock_interval_min)*1000;
        var $this = $(this);
        var t = setInterval(function() {
            update($this);
        }, interval);
        // start with a first one
        var t = setTimeout(function() {
            update($this);
        }, i*1000);
    });
});