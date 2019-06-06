Addcode='''
function(){
    _addEventListener = Element.prototype.addEventListener;
    var EVENT_LIST=new Array()
    Element.prototype.addEventListener = function(a,b,c){
        EVENT_LIST.push({"event":event, "element":this});
        _addEventListener.apply(this, arguments);
    };
    for (var i in EVENT_LIST){
        var evt = document.createEvent('CustomEvent');
        evt.initCustomEvent(EVENT_LIST[i]["event"], true, true, null);
        EVENT_LIST[i]["element"].dispatchEvent(evt);
    }
    console.log(EVENT_LIST)
    return EVENT_LIST
}
'''
Domcode='''
function(){
    var links = '';

    function trigger_inline() {
        var nodes = document.all;
        for (var i = 0; i < nodes.length; i++) {
            var attrs = nodes[i].attributes;
            for (var j = 0; j < attrs.length; j++) {
                attr_name = attrs[j].nodeName;
                attr_value = attrs[j].nodeValue;
                if (attr_name.substr(0, 2) == "on") {
                    console.log(attr_name + ' : ' + attr_value);
                    //eval(attr_value.split('return')[0] + ';');
                }
                if (attr_name in {
                    "src": 1,
                    "href": 1
                } && attrs[j].nodeValue.substr(0, 11) == "javascript:") {
                    console.log(attr_name + ' : ' + attr_value);
                    //eval(attr_value.substr(11).split('return')[0] + ';');
                }
            }
        }
    }
    trigger_inline();
    var getAbsoluteUrl = (function () {
        var a;
        return function (url) {
            if (!a) {
                a = document.createElement('a');
            }
            a.href = url;
            return a.href;
        };
    })();
    atags = document.getElementsByTagName("a");

    for (var i = 0; i < atags.length; i++) {
        if (atags[i].getAttribute("href")) {
            links += getAbsoluteUrl(atags[i].getAttribute("href")) + '***';
        }
    }
    iframetag = document.getElementsByTagName("iframe");
    for (var i = 0; i < iframetag.length; i++) {
        if (iframetag[i].getAttribute("src")) {
            links += getAbsoluteUrl(iframetag[i].getAttribute("src")) + '***';
        }
    }
    ftags = document.getElementsByTagName("form");
    for (var i = 0; i < ftags.length; i++) {
        var link = '';
        var action = getAbsoluteUrl(ftags[i].getAttribute("action"));
        if (action) {
            if (action.substr(action.length - 1, 1) == '#') {
                link = action.substr(0, action.length - 1);
            } else {
                link = action + '?';
            }
            for (var j = 0; j < ftags[i].elements.length; j++) {
                if (ftags[i].elements[j].tagName == 'INPUT') {
                    link = link + ftags[i].elements[j].name + '=';
                    if (ftags[i].elements[j].value == "" || ftags[i].elements[j].value == null) {
                        link = link + 'Abc123456!' + '&';
                    } else {
                        link = link + ftags[i].elements[j].value + '&';
                    }
                }
            }
        }
        links += link.substr(0, link.length - 1) + '***';
    }
    document.addEventListener('DOMNodeInserted', function(e) {
                var node = e.target;
                if(node.src || node.href){
                    links += (node.src || node.href)+'***';
                }
            }, true);
    return links;
}
'''

ajaxcode='''
function(){
    var ajax_LIST=new Array()
    XMLHttpRequest.prototype.__originalOpen =   XMLHttpRequest.prototype.open;  
    XMLHttpRequest.prototype.open   =   function(method,    url,    async,  user,   password)   {   
        //  hook    code
        ajax_LIST.push({"url":url});
        return this.__originalOpen(method,url,async,user,password);  
    }
    XMLHttpRequest.prototype.__originalSend    =   XMLHttpRequest.prototype.send;  
    XMLHttpRequest.prototype.send   =   function(data)  {   
        //  hook    code
        return this.__originalSend(data);  
    }
    return ajax_LIST;
}
'''