// Stock Ajax update
var update = function(link) {
    event.preventDefault();
    var id = $(link).attr('id');
    var url = "/update/code/"+id;
    console.log(url);
    $("#row-"+id).load(url);
}

$(document).ready(function() {
    // Automatic Ajax updates every 2-4 minutes
    $(".update").each(function(i){
        var interval = (Math.random()*120 + 120)*1000;
        var $this = $(this);
        var t = setInterval(function() {
            update($this);
        }, interval);
    });
});