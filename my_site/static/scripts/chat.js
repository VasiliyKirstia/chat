function ChatCore(){
    var _obj = {};
    
    //список ключей конференций
    _obj.conferences_pk_array = new Array();
    
    //словарь списков участников - ключи:pk конференций, значения: списки участников
    _obj.users_dict = {};
    
    //словарь количеств новых сообщений - ключи:pk конференций, значения: количество непрочитаных сообщений
    _obj.messages_count_dict = {};
    
    _obj.curent_conference_pk = undefined;
    _obj.last_message_time_stamp = 0;
    
    _obj.init = function(){
        $.ajax({
            url: '/chat/init/',
            async: true,
            type: 'POST',
            dataType: 'json',
            success: function(returnedData){
                $.each(returnedData,function(index,elem){
                    _obj.conferences_pk_array.push(elem['pk']);
                    _obj.users_dict[ elem['pk'] ] = elem['users'];
                    _obj.messages_count_dict[ elem['pk'] ] = elem['messages_count'];  
                });
            }
        });        
    };
    
    //возвращает структуру {ключ_конференции, список сообщений}
    _obj.get_new_messages = function(colback){
        $.ajax({
            url: '/chat/messages/',
            async: true,
            type: 'POST',
            data: {
                'conference_pk': _obj.curent_conference_pk,
                'message_time_stamp': _obj.last_message_time_stamp
            },
            dataType: 'json',
            success: function(returnedData){
                colback(returnedData);
            }
        });
    };
    
    _obj.get_messages_count = function(){
        $.ajax({
            url: '/chat/messages/',
            async: true,
            type: 'POST',
            data: {
                'list_conference_pk': JSON.stringify(_obj.conferences_pk_array)
            },
            dataType: 'json',
            success: function(returnedData){
                $.each(returnedData['old_conferences'],function(index, elem){
                    _obj.messages_count_dict[ elem['pk'] ] = elem['messages_count'];
                });
                $.each(returnedData['new_conferences'],function(index,elem){
                    _obj.conferences_pk_array.push(elem['pk']);
                    _obj.users_dict[ elem['pk'] ] = elem['users'];
                    _obj.messages_count_dict[ elem['pk'] ] = elem['messages_count'];  
                });
            }
        });
    };
    
    //возвращает структуру {conference_pk, users: [{username: is_online}] }
    _obj.get_users = function(colback){
        $.ajax({
            url: '/chat/users/',
            async: true,
            type: 'POST',
            data: {
                'conference_pk': _obj.curent_conference_pk,
            },
            dataType: 'json',
            success: function(returnedData){
                colback(returnedData);
            }
        });
    };
    
    //{conference_pk, users:[usernames]}
    _obj.create_conference = function(users_list, message, colback){
        $.ajax({
            url: '/chat/create_conference/',
            async: true,
            type: 'POST',
            data: {
                'users': JSON.stringify(users_list),
                'message': message
            },
            dataType: 'json',
            success: function(returnedData){
                colback(returnedData);
            }
        });
    };
    
    _obj.send = function(message){
        $.ajax({
            url: '/chat/send/',
            async: true,
            type: 'POST',
            data: {
                'conference_pk': _obj.curent_conference_pk,
                'message': message
            }
        });
    };
    
    _obj.leave = function(conference_pk){
        $.ajax({
            url: '/chat/leave/',
            async: true,
            type: 'POST',
            data: {
                'conference_pk': _obj.curent_conference_pk
            }
        });
    };
};