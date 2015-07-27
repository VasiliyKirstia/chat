function ServerAPI() {
    var _obj = {};

    //список ключей конференций
    _obj.conferences_pk_array = [];
    //проверяет наличие конференции в списке конференций
    _obj.conference_already_added = function(conference_pk){return (_obj.conferences_pk_array.indexOf(conference_pk) != -1);};

    //словарь списков участников - ключи:pk конференций, значения: списки участников
    _obj.users_dict = {};

    //словарь количеств новых сообщений - ключи:pk конференций, значения: количество непрочитаных сообщений
    _obj.messages_count_dict = {};

    _obj.init = function (onSuccess) {
        
        $.ajax({
            url: '/chat/init/',
            async: false,
            type: 'POST',
            dataType: 'json',
            success: function (returnedData) {
                $.each(returnedData, function (index, elem) {
                    _obj.conferences_pk_array.push(elem['pk']);
                    _obj.users_dict[elem['pk']] = elem['users'];
                    _obj.messages_count_dict[elem['pk']] = elem['messages_count'];
                });
                onSuccess();
            }
        });
    };

    //возвращает структуру {ключ_конференции, список сообщений}
    _obj.get_messages = function (curent_conference_pk, last_message_time_stamp, callback) {
        $.ajax({
            url: '/chat/messages/',
            async: true,
            type: 'POST',
            data: {
                'conference_pk': curent_conference_pk,
                'message_time_stamp': last_message_time_stamp
            },
            dataType: 'json',
            success: function (returnedData) {
                callback(returnedData);
            }
        });
    };
    
    _obj.get_new_messages_count = function (callback) {
        $.ajax({
            url: '/chat/messages_count/',
            async: true,
            type: 'POST',
            data: {
                'list_conference_pk': JSON.stringify(_obj.conferences_pk_array)
            },
            dataType: 'json',
            success: function (returnedData) {
                var new_conferences_pk_list = [];
                $.each(returnedData['old_conferences'], function (index, elem) {
                    _obj.messages_count_dict[elem['pk']] = elem['messages_count'];
                });
                $.each(returnedData['new_conferences'], function (index, elem) {
                    if( !_obj.conference_already_added(elem['pk']) ){
                        _obj.conferences_pk_array.push(elem['pk']);
                        _obj.users_dict[elem['pk']] = elem['users'];
                        _obj.messages_count_dict[elem['pk']] = elem['messages_count'];
                        new_conferences_pk_list.push(elem['pk']);
                    }
                });
                callback(new_conferences_pk_list);
            }
        });
    };

    //возвращает структуру {conference_pk, users: [{username: is_online}] }
    _obj.get_users = function (curent_conference_pk, callback) {
        $.ajax({
            url: '/chat/users/',
            async: true,
            type: 'POST',
            data: {
                'conference_pk': curent_conference_pk,
            },
            dataType: 'json',
            success: function (returnedData) {
                callback(returnedData);
            }
        });
    };

    //{conference_pk, users:[usernames]}
    _obj.create_conference = function (users_list, message, callback) {
        $.ajax({
            url: '/chat/create_conference/',
            async: false,
            type: 'POST',
            data: {
                'users': JSON.stringify(users_list),
                'message': message
            },
            dataType: 'json',
            success: function (returnedData) {
                if( !_obj.conference_already_added(returnedData['conference_pk']) ){
                    _obj.conferences_pk_array.push(returnedData['conference_pk']);
                    _obj.users_dict[returnedData['conference_pk']] = returnedData['users'];
                    _obj.messages_count_dict[returnedData['conference_pk']] = 0;
                    
                    callback(returnedData['conference_pk']);
                }
                callback(undefined);
            }
        });
    };

    _obj.send = function (message, curent_conference_pk, onSuccess) {
        $.ajax({
            url: '/chat/send/',
            async: true,
            type: 'POST',
            data: {
                'conference_pk': curent_conference_pk,
                'message': message
            },
            dataType: 'text',
            success: onSuccess
        });
    };

    _obj.leave = function (conference_pk) {
        $.ajax({
            url: '/chat/leave/',
            async: false,
            type: 'POST',
            data: {
                'conference_pk': conference_pk
            },
            dataType: 'text',
            success: function(){
                _obj.conferences_pk_array.splice(_obj.conferences_pk_array.indexOf(conference_pk), 1);
                delete _obj.users_dict[conference_pk];
                delete _obj.messages_count_dict[conference_pk];
            }
        });
    };
    return _obj;
};

function ChatGUI(_serverAPI) {
    var _obj = {};
        
    _obj.tabs_data = {};
    _obj.tabs_data.max_count = 4;
    _obj.tabs_data.active_tab_id = undefined;
    _obj.tabs_data.already_opened = [];
    
    _obj.tabs_data.is_already_opened = function(conference_pk){ return (_obj.tabs_data.already_opened.indexOf(conference_pk) != -1); };
    
    _obj.tabs_data.color_schemes = {
        0: 'primary',
        1: 'success',
        2: 'info',
        3: 'warning',
        4: 'danger'
    };
    _obj.tabs_data.color_schemes_count = Object.keys(_obj.tabs_data.color_schemes).length;
    
    _obj.update_information = {};
    _obj.update_information.message_idle_steps_count = 4;
    _obj.update_information.users_idle_steps_count = 32;
    _obj.update_information.message_count_idle_steps_count = 16;
    _obj.update_information.timeout = 500;  //ms

    
    _obj.GUIElements = {};
    _obj.GUIFunctions = {};
    
    
    _obj.GUIElements.tabpanels_container = $('#tabpanels-container');
    _obj.GUIElements.tabs_container = $('#tabs-container');
    _obj.GUIElements.message_send_textarea = $('#message-send-textarea');
    _obj.GUIElements.message_send_button = $('#message-send-button');
    
    _obj.GUIElements.conference_create_button = $('#conference-create-button')
    _obj.GUIElements.conference_create_textarea = $('#conference-create-textarea');
    _obj.GUIElements.conference_create_multiselect = $('#conference-create-multiselect');
    
    _obj.GUIElements.active_user_panels_container = $('#left-column')
    
    _obj.GUIElements.conferences_container = $('#conferences-container');
    
    _obj.GUIElements.new_messages_count = $('#new-messages-count');
    
    
    //добавляет конференцию со свойством data-id равным conference_pk
    _obj.GUIFunctions.add_conference = function(members_list, conference_pk, new_message_count){
        var name = members_list.length > 0 ? members_list.join(', ') : '*пустая*';
        
        if(new_message_count == 0){
             _obj.GUIElements.conferences_container.append(
                    '<div class="alert alert-success alert-dismissible" role="alert">'+
                    '<button type="button" class="close" data-dismiss="alert" aria-label="Close" data-id="'+ conference_pk +'">'+
                    '<span aria-hidden="true"><i class="glyphicon glyphicon-remove"></i></span>'+
                    '</button>'+
                    '<a class="badge" data-id="'+ conference_pk +'">новых нет</a> ' + name +
                    '</div>');  
        }else{
            _obj.GUIElements.conferences_container.prepend(
                    '<div class="alert alert-danger alert-dismissible" role="alert">'+
                    '<button type="button" class="close" data-dismiss="alert" aria-label="Close" data-id="'+ conference_pk +'">'+
                    '<span aria-hidden="true"><i class="glyphicon glyphicon-remove"></i></span>'+
                    '</button>'+
                    '<a class="badge" data-id="'+ conference_pk +'">' + new_message_count + ((new_message_count%10==1 && new_message_count != 11)?' новое':' новых') + '</a> ' + name +
                    '</div>');   
        }
        
    };
    
    //добавляет сообщение во вкладку с id равным conference_pk 
    _obj.GUIFunctions.add_message = function(sender, color_scheme, message, conference_pk){
        var message_container = _obj.GUIElements.tabpanels_container.find('#' + conference_pk);
            message_container.append(
                '<div class="well well-sm" style="overflow-x:auto;"><span class="label label-'+ color_scheme +'">'+ sender +'</span> '+message+' </div>'
            );
    };
    
    //добавляет пользователя с учетом его статуса
    _obj.GUIFunctions.add_user = function(username, is_online, container){
        if(is_online){
            container.append(
                    '<li class="list-group-item list-group-item-success">'+
                    '<i class="glyphicon glyphicon-ok-circle"></i> ' + username +
                    '</li>');
        }else{
            container.append(
                    '<li class="list-group-item list-group-item-danger">'+
                    '<i class="glyphicon glyphicon-remove-circle"></i> ' + username +
                    '</li>');
        }
    };
    
    //добавляет вкладку с id равным conference_pk и панель участников с id равным members-panel-[conference_pk]
    _obj.GUIFunctions.add_tab = function(tab_name, conference_pk){
        //флаг позволяющий определить нужно ли запускать пузырь для этой конференции
        var booble_already_created = false;
        //если не исчерпан лимит одновременно открытых вкладок
        if(_obj.tabs_data.already_opened.length < _obj.tabs_data.max_count ){
            //если эта конференция еще не открыта
            if( !_obj.tabs_data.is_already_opened(conference_pk) ){
                
                _obj.tabs_data.already_opened.push(conference_pk);
                
                var tab = $(
                    '<li role="presentation" class="active">'+
                    '<a href="#'+conference_pk+'" aria-controls="home" role="tab" data-toggle="tab" data-id="'+conference_pk+'">' + tab_name +
                    '</a>'+
                    '</li>'
                );
                
                var tabpanel = $(
                    '<div role="tabpanel" class="tab-pane active" id="'+ conference_pk +'" style="height: calc(100vh - 225px);overflow-y: auto;"></div>'
                );
                
                var userpanel = $(
                    '<div class="panel panel-primary hidden-xs" id="members-panel-' + conference_pk + '">' +
                    '<div class="panel-heading">Участники конференции</div>'+
                    '<ul class="list-group" style="max-height: calc(100vh - 240px);overflow-y: auto;">'+
                    '</ul>'+
                    '</div>'
                );

                if(_obj.tabs_data.active_tab_id != undefined){
                    _obj.GUIElements.tabs_container.find('li.active').removeClass('active');
                    _obj.GUIElements.tabpanels_container.find('#' + _obj.tabs_data.active_tab_id).removeClass('active');
                    _obj.GUIElements.active_user_panels_container.find('#members-panel-' + _obj.tabs_data.active_tab_id).addClass('hide');
                }

                _obj.GUIElements.tabs_container.append(tab);
                _obj.GUIElements.tabpanels_container.append(tabpanel);
                _obj.GUIElements.active_user_panels_container.append(userpanel);
                
                _obj.tabs_data.active_tab_id = conference_pk;
            }else{
                //эта конференция уже открыта, по этому тут ничего не делаем
                booble_already_created = true;
                return;
            }
        //лимит вкладок исчерпан
        }else{
            //если вкладка еще не открыта то открываем её вместо текущей активной
            if( !_obj.tabs_data.is_already_opened(conference_pk) ){
                _obj.tabs_data.already_opened[_obj.tabs_data.already_opened.indexOf(_obj.tabs_data.active_tab_id)] = conference_pk;
                
                var tab = _obj.GUIElements.tabs_container.find('a[href="#'+_obj.tabs_data.active_tab_id+'"]');
                tab.attr('data-id', conference_pk);
                tab.attr('href', '#'+conference_pk);
                tab.text(tab_name); 

                var tabpanel = _obj.GUIElements.tabpanels_container.find('#' + _obj.tabs_data.active_tab_id);
                tabpanel.attr('id', conference_pk);
                tabpanel.html('');

                var userpanel = _obj.GUIElements.active_user_panels_container.find('#members-panel-' + _obj.tabs_data.active_tab_id);
                userpanel.attr('id', 'members-panel-' + conference_pk);
                userpanel.find('ul').html('');
                
                _obj.tabs_data.active_tab_id = conference_pk;
            }else{
                //конференция уже открыта
                booble_already_created = true;
            }
        }
        
        
        /*
        *   Фабрика пузырей для обновления информации о участниках конференции.
        *   При открытии конференции во вкладке запускаем пузырь.
        *   Пока вкладка активна пузырь обновляет для нее информацию о пользователях.
        *   Пока вкладка открыта но не активна пузырь просто продолжает существование не обновляя ничего.
        *   Как только вкладка закрывается пузырь перестает существовать.
        */
        (function(){
            //если вкладка уже открыта то для нее уже создан пузырь
            if(booble_already_created){
                return;
            }
            
            var my_conference_pk = conference_pk;
            var current_step_number = -1;
            var my_userpanel = _obj.GUIElements.active_user_panels_container.find('#members-panel-' + my_conference_pk).find('ul');
            var bubble = function(){
                if( !_obj.tabs_data.is_already_opened(my_conference_pk) ) {
                    return;
                }
                
                if( _obj.tabs_data.active_tab_id != my_conference_pk ){
                    setTimeout(bubble, _obj.update_information.timeout);
                    return;
                }
                
                current_step_number = (current_step_number + 1) % _obj.update_information.users_idle_steps_count;
                if(current_step_number != 0){
                    setTimeout(bubble, _obj.update_information.timeout);
                    return;
                }
            
                _serverAPI.get_users(my_conference_pk, function(returnedData){
                    var $container = $("<div></div>");
                    $.each(returnedData, function(index, elem){
                        _obj.GUIFunctions.add_user(elem[0], elem[1], $container);
                    });
                    my_userpanel.html($container.html());
                });
                
                setTimeout(bubble, _obj.update_information.timeout);
            };
            bubble();
        })();
        
        /*
        *   Фабрика пузырей для получения новых сообщений.
        *   При открытии конференции во вкладке запускаем пузырь.
        *   Пока вкладка активна пузырь запрашивает новые сообщения.
        *   Пока вкладка открыта но не активна пузырь просто продолжает существование не запрашивая ничего.
        *   Как только вкладка закрывается пузырь перестает существовать.
        */
        (function(){
            //если вкладка уже открыта то для нее уже создан пузырь
            if(booble_already_created){
                return;
            }
            
            var current_step_number = -1;
            var my_conference_pk = conference_pk;
            var my_last_message = 0;
            var my_color_schemes_dict = {};
            $.each(_serverAPI.users_dict[my_conference_pk], function(index, elem){
                my_color_schemes_dict[elem] = _obj.tabs_data.color_schemes[index % _obj.tabs_data.color_schemes_count];
            });
            
            var bubble = function(){
                if( !_obj.tabs_data.is_already_opened(my_conference_pk) ) {
                    return;
                }
                
                if( _obj.tabs_data.active_tab_id != my_conference_pk ){
                    setTimeout(bubble, _obj.tabs_data.message_update_timeout);
                    return;
                }
                
                current_step_number = (current_step_number + 1) % _obj.update_information.message_idle_steps_count;
                if(current_step_number != 0){
                    setTimeout(bubble, _obj.update_information.timeout);
                    return;
                }
                
                _serverAPI.get_messages(my_conference_pk, my_last_message, function(returnedData){
                    $.each(returnedData, function(index, elem){
                        if(my_last_message < elem['time_stamp']){
                            my_last_message = elem['time_stamp'];
                        }
                        
                        if( Object.keys(my_color_schemes_dict).indexOf(elem['sender']) == -1 ){
                            my_color_schemes_dict[elem['sender']] = _obj.tabs_data.color_schemes[Object.keys(my_color_schemes_dict).length % _obj.tabs_data.color_schemes_count];
                        }
                        
                        _obj.GUIFunctions.add_message(elem['sender'], my_color_schemes_dict[elem['sender']], elem['message'], my_conference_pk);
                    });
                });
                
                setTimeout(bubble, _obj.tabs_data.user_update_timeout);
            };
            bubble();
        })();
    };

    return _obj;
};

$(document).ready(function(){
    var _serverAPI = ServerAPI();
    var _chatGUI = ChatGUI(_serverAPI);
    
    //инициализация чата
    _serverAPI.init(function(){
       $.each(_serverAPI.conferences_pk_array, function(index, conference_pk){
           _chatGUI.GUIFunctions.add_conference(_serverAPI.users_dict[conference_pk],conference_pk,_serverAPI.messages_count_dict[conference_pk]);
       });
    });
    
    //открытие конференции во вкладке
    _chatGUI.GUIElements.conferences_container.on('click', 'a.badge', function(eventObj){
        var conference_pk = parseInt( $(eventObj.currentTarget).data('id') );
        var tab_name = _serverAPI.users_dict[conference_pk].length > 0 ? _serverAPI.users_dict[conference_pk].join(', ') : '*пустая*';       
        _chatGUI.GUIFunctions.add_tab(tab_name, conference_pk);
    });
    
    //переключение вкладок
    _chatGUI.GUIElements.tabs_container.on('click', 'a', function(eventObj){
        _chatGUI.GUIElements.active_user_panels_container.find('#members-panel-' + _chatGUI.tabs_data.active_tab_id).addClass('hide');
        _chatGUI.tabs_data.active_tab_id = parseInt( $(eventObj.currentTarget).data('id'));
        _chatGUI.GUIElements.active_user_panels_container.find('#members-panel-' + _chatGUI.tabs_data.active_tab_id).removeClass('hide');
    });
    
    //отправка сообщений
    _chatGUI.GUIElements.message_send_button.click(function(eventObj){
        var message = (_chatGUI.GUIElements.message_send_textarea.val()).trim();
        if(message.length == 0) return;
        if(_chatGUI.tabs_data.active_tab_id == undefined) return;
        
        _serverAPI.send(message, _chatGUI.tabs_data.active_tab_id, function(){
            _chatGUI.GUIElements.message_send_textarea.val('');
        });
    });
    
    //создание конференции
    _chatGUI.GUIElements.conference_create_button.click(function(eventObj){
        var users_list = _chatGUI.GUIElements.conference_create_multiselect.val();
        var message = (_chatGUI.GUIElements.conference_create_textarea.val()).trim();
        
        if(users_list === null || message.length == 0){
            return;
        }
        
        _serverAPI.create_conference(users_list, message, function(conference_pk){
            if(conference_pk != undefined){
                _chatGUI.GUIFunctions.add_conference(_serverAPI.users_dict[conference_pk],conference_pk,_serverAPI.messages_count_dict[conference_pk]);
                _chatGUI.GUIElements.conferences_container.find('a[data-id='+conference_pk+']').click();
                _chatGUI.GUIElements.conference_create_textarea.val('');
            }
        });
    });
    
    //удаление конференции
    _chatGUI.GUIElements.conferences_container.on('click', 'button.close', function(eventObj){
        var conference_pk = parseInt( $(eventObj.currentTarget).data('id') );
        if( !_serverAPI.conference_already_added(conference_pk) ){
            return;
        }
        
        _serverAPI.leave(conference_pk);
        
        var index_of_elem = _chatGUI.tabs_data.already_opened.indexOf(conference_pk);
        if(index_of_elem != -1){
            _chatGUI.tabs_data.already_opened.splice(index_of_elem, 1);
            if(_chatGUI.tabs_data.active_tab_id == conference_pk){
                _chatGUI.tabs_data.active_tab_id = undefined;    
            }          
            
            _chatGUI.GUIElements.tabs_container.find('li > a[data-id='+conference_pk+']').parent().remove()
            _chatGUI.GUIElements.tabpanels_container.find('#'+conference_pk).remove()
            _chatGUI.GUIElements.active_user_panels_container.find('#members-panel-'+conference_pk).remove();
            
            if(_chatGUI.tabs_data.already_opened.length > 0){
                _chatGUI.GUIElements.tabs_container.find('a[data-id='+_chatGUI.tabs_data.already_opened[0]+']').click();
            }
        }
    });
    
    //получение количества новых сообщений и новых конференций
    (function(){
        var current_step_number = -1;
        var bubble = function(){
            current_step_number = (current_step_number + 1) % _chatGUI.update_information.message_count_idle_steps_count;
            if(current_step_number != 0){
                setTimeout(bubble, _chatGUI.update_information.timeout);
                return;
            }
            
            _serverAPI.get_new_messages_count(function(new_conferences_pk_list){
                $.each(new_conferences_pk_list, function(index, elem){
                        _chatGUI.GUIFunctions.add_conference(_serverAPI.users_dict[elem],elem,_serverAPI.messages_count_dict[elem]);       
                });
                
                var total_new_messages_count = 0;
                var cur_conf_a;
                var cur_mc;
                $.each(_serverAPI.conferences_pk_array, function(index, elem){
                    cur_mc = _serverAPI.messages_count_dict[elem];
                    total_new_messages_count+=cur_mc;
                    
                    cur_conf_a = _chatGUI.GUIElements.conferences_container.find('a[data-id='+elem+']');
                    cur_conf_a.parent().removeClass('alert-danger');
                    cur_conf_a.parent().removeClass('alert-success');
                    cur_conf_a.parent().addClass( (cur_mc > 0 ? 'alert-danger' : 'alert-success') );
                    
                    cur_conf_a.text(  (cur_mc==0?'новых нет':(cur_mc + ((cur_mc%10==1 && cur_mc != 11)?' новое':' новых'))) );
                });
                _chatGUI.GUIElements.new_messages_count.text(total_new_messages_count);
            });
    
            setTimeout(bubble, _chatGUI.new_message_counts_update_timeout);
        };
        bubble();
    })();

    $('#conference-create-multiselect').chosen({
        width: "100%",
        no_results_text: "Мы не нашли ничего похожего на "
    });
    $("#conference-create-multiselect").trigger("chosen:updated");
    
    var _keylogger = Keylogger(); 
    _keylogger.init(_chatGUI.GUIElements.message_send_textarea);
    _chatGUI.GUIElements.message_send_button.on("click", _keylogger.send);

});
//todo: проблема с установкой active_tab_id, проблема с открытием конференций во вкладках, проблема с переключением вкладок.