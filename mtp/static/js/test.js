/***** 
 * 作者：<span style="font-family:Arial, Helvetica, sans-serif;font-size:12px;">jww_dragon</span><span style="font-family:Arial, Helvetica, sans-serif;font-size:12px;">@</span><span style="font-family:Arial, Helvetica, sans-serif;font-size:12px;">163.com</span><span style="font-family:Arial, Helvetica, sans-serif;font-size:12px;"> 
</span> * 依赖: jquery 
 *  
 ********************/  
  
var goog = function(tag) {  
    this._hotpoint = [];  
    this._square = {};  
    if (typeof tag === "string") {  
        this.canvas = document.getElementById(tag);  
    } else {  
        this.canvas = tag;  
    }  
    this.context = this.canvas.getContext('2d');  
    this.colorStyle = {};  
    this.colorStyle.selectColor = "rgba(255,0,0,0.8)";  
    this.colorStyle.selectedColor = "rgba(255,0,0,0.3)";  
    this.colorStyle.showColorBG = "rgba(0,0,0,0.2)";  
    this.colorStyle.shadowColor = "#000000";  
    this.colorStyle.fontStyle = "16px Arial Black";  
    this.colorStyle.fontColor = "yellow";  
    this.context.shadowOffsetX = 5;  
    this.context.shadowOffsetY = 5;  
    this.context.shadowBlur = 10;  
}  
  
/** 
 *换一个id监听（一般用不到） 
 **/  
goog.prototype.listen = function(documentId) {  
    this.canvas = document.getElementById(documentId);  
    this.canvas = document.getElementById(documentId);  
    this.context = this.canvas.getContext('2d')  
}  
  
/** 
 *颜色配置 
 * selectColor,selectedColor 框选颜色，默认红色， showColorBG 展示的背景蒙层色 
 * shadowColor 影阴颜色，fontStyle 字体,fontColor 字体颜色 
 **/  
goog.prototype.setColor = function(type, color) {  
    if (typeof color != "undefined" && type != "undefined") {  
        this.colorStyle[type] = color;  
    }  
}  
  
/** 
 * 以下是选择部分 
 ***/  
goog.prototype.init_mask = function() {  
    var position_top = this.canvas.offsetTop;  
    var position_left = this.canvas.offsetLeft;  
    this.temp_canvas = document.createElement("canvas");  
    this.temp_canvas.setAttribute('width', this.canvas.width);  
    this.temp_canvas.setAttribute('id', "mask-gogo123");  
    this.temp_canvas.setAttribute('height', this.canvas.height);  
    this.temp_canvas.setAttribute('style', 'position: absolute;left: '  
            + position_left + 'px;top: ' + position_top + 'px;');  
    this.canvas.parentNode.appendChild(this.temp_canvas);  
    //return temp_canvas;  
}  
goog.prototype.drowInitSquare = function(_list) {  
    this.context.shadowColor = this.colorStyle.shadowColor;  
    this.context.font = this.colorStyle.fontStyle;  
    //this.context.strokeStyle=this.colorStyle.fontColor;  
    for ( var _i in _list) {  
        this.context.fillStyle = this.colorStyle.selectedColor;  
        this.context.fillRect(_list[_i].x, _list[_i].y, _list[_i].w,  
                _list[_i].h);  
        //这里是业务需求eventName现示出来  
        if (!!_list[_i].eventName) {  
            this.context.fillStyle = this.colorStyle.fontColor;  
            var font_w = (_list[_i].w - this.context  
                    .measureText(_list[_i].eventName).width) / 2;  
            if (font_w < 2)  
                font_w = 2;  
            this.context.fillText(_list[_i].eventName, _list[_i].x + font_w,  
                    (_list[_i].y + _list[_i].h / 2 + 4), _list[_i].w - 5);  
        }  
    }  
    this.context.closePath();  
}  
  
goog.prototype.selectDetermine = function(opt) {  
    if (typeof this.temp_canvas.tempSquare == "undefined") {  
        return;  
    }  
    var select_condtion = {};  
    if (typeof opt != "undefined") {  
        $.extend(select_condtion, opt);  
    }  
    this._square = this.temp_canvas.tempSquare;  
    this.context.shadowColor = this.colorStyle.shadowColor;  
    this.context.fillStyle = this.colorStyle.selectedColor;  
    this.context.fillRect(this._square.x, this._square.y, this._square.w,  
            this._square.h);  
    this.context.closePath();  
  
    //要用到jquery的就这么一处，如果实在不要jquery就自己写继承方法  
    $.extend(select_condtion, this._square);  
    //可以不要的  
    select_condtion.uuid = this._hotpoint.length + "_"  
            + Math.floor(Math.random() * 10000);  
    this._hotpoint.push(select_condtion);  
    var k = "Coordinate range is generated:" + this._square.x + ','  
            + this._square.y + ',' + (this._square.x + this._square.w) + ','  
            + (this._square.y + this._square.h);  
    console.log(k);  
}  
/** 
 * 这个很重要，找了好久，才看见有个老外的回答，不然坐标会偏移 
 */  
function goog_findPos(obj) {  
    var curleft = 0, curtop = 0;  
    if (obj.offsetParent) {  
        do {  
            curleft += obj.offsetLeft;  
            curtop += obj.offsetTop;  
        } while (obj = obj.offsetParent);  
        return {  
            x : curleft,  
            y : curtop  
        };  
    }  
    return undefined;  
}  
  
goog.prototype.selectListen = function() {  
    this.init_mask();  
    var temp_context = this.temp_canvas.getContext('2d');  
    temp_context.strokeStyle = this.colorStyle.selectColor;  
    var genCoordinate = this.genCoordinates;  
    var f1 = {}, f2 = {};  
    this.temp_canvas.onmousedown = function(_e) {  
        var pos = goog_findPos(this);  
        f1.layerX = _e.pageX - pos.x;  
        f1.layerY = _e.pageY - pos.y;  
        this.onmousemove = function(e) {  
            temp_context.clearRect(0, 0, this.width, this.height);  
            f2.layerX = e.pageX - pos.x;  
            f2.layerY = e.pageY - pos.y;  
            var square = genCoordinate(f1, f2);  
            temp_context.roundRect(square.x, square.y, square.w, square.h);  
        };  
        this.onmouseup = function(e) {  
            this.onmousemove = null;  
            this.onmouseup = null;  
            f2.layerX = e.pageX - pos.x;  
            f2.layerY = e.pageY - pos.y;  
            this.tempSquare = genCoordinate(f1, f2);  
        };  
    }  
}  
  
goog.prototype.getSelected = function() {  
    return this._hotpoint;  
}  
  
/** 
 * 以下是展示部分 
 ***/  
goog.prototype.setHotpoint = function(_datas) {  
    if (typeof _datas != "undefined") {  
        this._hotpoint = _datas;  
    }  
}  
goog.prototype.showListen = function() {  
    this.addShowListen(this._hotpoint);  
}  
goog.prototype.addShowListen = function(_datas) {  
    this.canvas.context = this.context;  
    this.canvas.googColorStyle = this.colorStyle;  
    var _show = this.show;  
    var _showDiv = this.showDiv;  
    this.goog_DataFormat(_datas);  
    this.createDiv(this.canvas, _datas);  
    var f = {};  
    this.canvas.onmouseover = function(e) {  
        this.context.fillStyle = this.googColorStyle.showColorBG;  
        this.context.shadowColor = this.googColorStyle.shadowColor;  
        this.context.fillRect(0, 0, this.width, this.height);  
        _show(this.context, _datas);  
    };  
    this.canvas.onmouseout = function(e) {  
        this.context.closePath();  
        this.context.clearRect(0, 0, this.width, this.height);  
    };  
    this.canvas.onmousemove = function(e) {  
        var pos = goog_findPos(this);  
        f.layerX = e.pageX - pos.x;  
        f.layerY = e.pageY - pos.y;  
        if (this.context.isPointInPath(f.layerX, f.layerY)) {  
            for ( var cirle in _datas) {  
                var amt = _datas[cirle];  
                if (f.layerX > Math.min(amt.x, amt.x + amt.w)  
                        && f.layerX < Math.max(amt.x, amt.x + amt.w)  
                        && f.layerY > Math.min(amt.y, amt.y + amt.h)  
                        && f.layerY < Math.max(amt.y, amt.y + amt.h)) {  
  
                    $("#goog_poop_" + amt.uuid).show();  
                }  
            }  
        } else {  
            $('.goog_tag_v').hide();  
        }  
    };  
}  
/** 
 *用来现实展示具体值的DIV 
 ***/  
goog.prototype.createDiv = function(canvas, _datas) {  
    $('.goog_tag_v').remove();  
    var position_top = canvas.offsetTop;  
    var position_left = canvas.offsetLeft;  
    for ( var i in _datas) {  
        var amt = _datas[i];  
        var _tag = document.createElement("div");  
        _tag.setAttribute('id', "goog_poop_" + amt.uuid);  
        _tag.setAttribute('class', "goog_tag_v");  
        _tag.setAttribute('width', 300);  
        _tag.setAttribute('height', 50);  
        _tag.setAttribute('style',  
                'display:none;background:#000; color:#FFF; position: absolute;left: '  
                        + (position_left + amt.x) + 'px;top: '  
                        + (position_top + amt.y) + 'px;');  
        _tag.innerText = "数量:" + amt.data;  
        canvas.parentNode.appendChild(_tag);  
        //或则加名字什么的  
    }  
  
}  
  
goog.prototype.destroy = function() {  
    this.canvas.remove();  
    if (typeof this.temp_canvas != "undefined") {  
        this.temp_canvas.remove();  
    }  
    this._hotpoint = [];  
    this._square = {};  
}  
  
goog.prototype.showListenDestroy = function() {  
    this.canvas.onmousemove = null;  
    this.canvas.onmouseover = null;  
    this.canvas.onmouseout = null;  
}  
  
//预留，万一要转换数组型到类对象  
goog.prototype.goog_DataFormat = function(_datas) {  
    if (_datas.length <= 0) {  
        return;  
    }  
    var sum = 0  
      
    for ( var _i in _datas) {  
        if (typeof _datas[_i].x == "undefined") {  
            //预留，万一要转换数组型到类对象  
            return;  
        }  
        //业务  
        _datas[_i].data = _datas[_i].eventAmount;  
        if (typeof _datas[_i].data == "undefined") {  
            //DEMO 用  
            _datas[_i].data = Math.random() * 100;  
        }  
        sum = sum + _datas[_i].data;  
    }  
    var avg = sum / _datas.length;  
    //分段函数，看情况,这是业务逻辑了  
    for ( var _i in _datas) {  
        if (_datas[_i].data / avg > 1.5) {  
            _datas[_i].type = 1;  
        } else if (_datas[_i].data / avg >= 1) {  
            _datas[_i].type = 2;  
        } else if (_datas[_i].data / avg >= 0.5) {  
            _datas[_i].type = 3;  
        } else {  
            _datas[_i].type = 4;  
        }  
    }  
}  
  
goog.prototype.show = function(context, _datas) {  
    if (typeof _datas == "undefined") {  
        return;  
    }  
    if (typeof _datas == null) {  
        return;  
    }  
    if (_datas.length <= 0) {  
        return;  
    }  
    for ( var _i in _datas) {  
        cirle = _datas[_i];  
        var r = Math.min(cirle.h, cirle.w) / 2;  
        r = Math.min(r, 50); //最大半径为50 ,以后半径可以和data的大小有关  
        //中心点确定.渐变  
        my_gradient = context.createRadialGradient((cirle.x + cirle.w / 2),  
                (cirle.y + cirle.h / 2), 0, (cirle.x + cirle.w / 2),  
                (cirle.y + cirle.h / 2), r);  
        if (cirle.type == 1) {  
            my_gradient.addColorStop(0.0, "rgba(255,0,0,0.8)"); //定义红色渐变色  
            my_gradient.addColorStop(0.3, "rgba(255,255,0,0.7)"); //定义黄色渐变色  
            my_gradient.addColorStop(0.6, "rgba(0,255,0,0.5)"); //定义绿色渐变色  
            my_gradient.addColorStop(0.9, "rgba(0,0,255,0.2)"); //定义蓝色渐变色           
        } else if (cirle.type == 2) {  
            my_gradient.addColorStop(0.3, "rgba(255,255,0,0.7)"); //定义黄色渐变色  
            my_gradient.addColorStop(0.6, "rgba(0,255,0,0.5)"); //定义绿色渐变色  
            my_gradient.addColorStop(0.9, "rgba(0,0,255,0.3)"); //定义蓝色渐变色  
        } else if (cirle.type == 3) {  
            my_gradient.addColorStop(0.2, "rgba(0,255,0,0.5)"); //定义绿色渐变色  
            my_gradient.addColorStop(0.7, "rgba(0,0,255,0.4)"); //定义蓝色渐变色  
        } else {  
            my_gradient.addColorStop(0.3, "rgba(0,0,255,0.6)"); //定义蓝色渐变色  
        }  
  
        my_gradient.addColorStop(1, "rgba(0,0,0,0)"); //定义黑色渐变色  
        context.fillStyle = my_gradient;  
        context.arc((cirle.x + cirle.w / 2), (cirle.y + cirle.h / 2), r, 0,  
                Math.PI * 2, true);  
        context.fill();  
    }  
}  
  
/** 
 * 以下是工具类 
 ***/  
//必须保证在第三象限，不然后面的都要出错。  
goog.prototype.genCoordinates = function(_e, e) {  
    var square = {};  
    var x = _e.layerX;  
    var x2 = e.layerX;  
    var y = _e.layerY;  
    var y2 = e.layerY;  
    var w = x2 - x;  
    var h = y2 - y;  
    if (w < 0) {  
        w = 0 - w;  
        x = x2;  
    }  
    if (h < 0) {  
        h = 0 - h;  
        y = y2;  
    }  
    square.x = x;  
    square.y = y;  
    square.w = w;  
    square.h = h;  
    return square;  
}  
  
//圆弧函数，补充的，也可以用方块函数/  
CanvasRenderingContext2D.prototype.roundRect = function(x, y, width, height,  
        radius, stroke) {  
    if (typeof stroke == "undefined") {  
        stroke = true;  
    }  
    if (typeof radius === "undefined") {  
        radius = 5;  
    }  
    this.beginPath();  
    this.moveTo(x + radius, y);  
    this.lineTo(x + width - radius, y);  
    this.quadraticCurveTo(x + width, y, x + width, y + radius);  
    this.lineTo(x + width, y + height - radius);  
    this  
            .quadraticCurveTo(x + width, y + height, x + width - radius, y  
                    + height);  
    this.lineTo(x + radius, y + height);  
    this.quadraticCurveTo(x, y + height, x, y + height - radius);  
    this.lineTo(x, y + radius);  
    this.quadraticCurveTo(x, y, x + radius, y);  
    this.closePath();  
    if (stroke) {  
        this.stroke();  
    }  
};  