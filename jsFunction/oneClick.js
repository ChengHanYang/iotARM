/**
 * Created by lumpa on 2016/10/29.
 */
$(document).ready(function () {
    function getRequest(direct) {
        $.ajax({
            type: "GET",
            url: "phpFunction/mysql_iot.php?move=" + direct,
            dataType: "json",
            success: function (data) {
                if (data.result) {
                    $("#show-data").html(
                        "您的位置在:<br>X=" + data.sql['movX'] + ", Y=" + data.sql['movY']
                    );
                } else {
                    $("#show-data").html('fuck');
                }
            },
            error: function (jqXHR) {
                alert("發生錯誤: " + jqXHR.status);
            }
        });
    }

    $('.arrow').click(function(){
        getRequest($(this).attr('arrow'));
    });
});