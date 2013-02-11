(function() {

function init() {
  $('#intro').on('click', 'button', function() {
    var happy = $(this).hasClass('happy');
    $('#intro').addClass('prev');
    $('#moreinfo').removeClass('next').addClass(happy ? 'happy' : 'sad');
    $('#moreinfo input[name=happy]').val(happy? '1' : '0');
    history.pushState({}, "", "#" + (happy ? 'happy' : 'sad'));
  });

  $('#moreinfo button.back').on('click', function() {
    $('#moreinfo').addClass('next').removeClass('happy sad');
    $('#intro').removeClass('prev');
  });

  $('#moreinfo .email-ok input').on('change', function() {
    var on = $(this).is(':checked');
    $('#moreinfo .email').toggle(on);
    $('#privacy-email').toggle(on);
  });
  $('#moreinfo .email-ok input').change();

  if (window.location.hash === '#happy') {
    $('#intro').addClass('prev');
    $('#moreinfo').addClass('happy');
    $('#moreinfo input[name=happy]').val('1');
  } else if (window.location.hash === '#sad') {
    $('#intro').addClass('prev');
    $('#moreinfo').addClass('sad');
    $('#moreinfo input[name=happy]').val('0');
  } else {
    $('#moreinfo').addClass('next');
  }

  $('#intro, #moreinfo').show();
}

$(init);

})();
