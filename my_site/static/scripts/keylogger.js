function Keylogger(){
    var _obj = {}

    _obj.log = {
        key_press: [],
        key_release: []
    };

    _obj.init = function(element){
        $(element).on('keyup', function(eventObj){
            _obj.log.key_press.push({
                key_code: eventObj.keyCode,
                time: $.now()
            });
        });

        $(element).on('keydown', function(eventObj){
            _obj.log.key_release.push({
                key_code: eventObj.keyCode,
                time: $.now()
            });
        });
    }

    _obj.send = function(){
        $.ajax({
            async: true,
            type: 'POST',
            data: {
                data: JSON.stringify(_obj.log)
            },
            //dataType: 'json',
            url:'/secret_research/send_pack/',
            success: function(){
                _obj.log = {
                    key_press: [],
                    key_release: []
                };
            },
        });
    };
    return _obj;
};