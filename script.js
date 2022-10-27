function backToTop() {
    var x1 = x2 = x3 = 0;
    var y1 = y2 = y3 = 0;

    if (document.documentElement) {
        x1 = document.documentElement.scrollLeft || 0;
        y1 = document.documentElement.scrollTop || 0;
    }

    if (document.body) {
        x2 = document.body.scrollLeft || 0;
        y2 = document.body.scrollTop || 0;
    }

    x3 = window.scrollX || 0;
    y3 = window.scrollY || 0;

    var x = Math.max(x1, Math.max(x2, x3));
    var y = Math.max(y1, Math.max(y2, y3));

    window.scrollTo(Math.floor(x / 1.5), Math.floor(y / 1.5));

    if (x > 0 || y > 0) {
        window.setTimeout("backToTop()", 25);
    }
}

var j$ = jQuery;

j$(function(){
	j$(".side_menu").each(function(){
		j$("li > a", this).each(function(index){
			var $this = j$(this);
			if(index > 0) $this.next().hide();

			$this.mousedown(function(){
				var params = {height:"toggle", opacity:"toggle"};
				j$(this).next().animate(params).parent().siblings()
				.children("ul:visible").animate(params);	

				return false;				

			});
		});
	});
});

$(function() {
    $('#nav').droppy({speed: 200});
  });
  
/*
 * Droppy 0.1.2
 * (c) 2008 Jason Frame (jason@onehackoranother.com)
 */
$.fn.droppy = function(options) {
    
  options = $.extend({speed: 250}, options || {});
  
  this.each(function() {
    
    var root = this, zIndex = 1000;
    
    function getSubnav(ele) {
      if (ele.nodeName.toLowerCase() == 'li') {
        var subnav = $('> ul', ele);
        return subnav.length ? subnav[0] : null;
      } else {
        return ele;
      }
    }
    
    function getActuator(ele) {
      if (ele.nodeName.toLowerCase() == 'ul') {
        return $(ele).parents('li')[0];
      } else {
        return ele;
      }
    }
    
    function hide() {
      var subnav = getSubnav(this);
      if (!subnav) return;
      $.data(subnav, 'cancelHide', false);
      setTimeout(function() {
        if (!$.data(subnav, 'cancelHide')) {
          $(subnav).slideUp(options.speed);
        }
      }, 500);
    }
  
    function show() {
      var subnav = getSubnav(this);
      if (!subnav) return;
      $.data(subnav, 'cancelHide', true);
      $(subnav).css({zIndex: zIndex++}).slideDown(options.speed);
      if (this.nodeName.toLowerCase() == 'ul') {
        var li = getActuator(this);
        $(li).addClass('hover');
        $('> a', li).addClass('hover');
      }
    }
    
    $('ul, li', this).hover(show, hide);
    $('li', this).hover(
      function() { $(this).addClass('hover'); $('> a', this).addClass('hover'); },
      function() { $(this).removeClass('hover'); $('> a', this).removeClass('hover'); }
    );
    
  });
  
};
