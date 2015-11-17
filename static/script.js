$(document).ready(function() {

  $('.js-feed-edit').click(function() {
    feedId = $(this).data('feed-id')
    name = $('.js-feed-name[data-feed-id="' + feedId + '"]').text()

    nameInput = $('<input>')
      .addClass('form-control js-feed-name-edit')
      .attr('form', 'feed-form')
      .attr('data-feed-id', feedId)
      .val(name)

    $('.js-feed-name[data-feed-id="' + feedId + '"]').html(nameInput)
  })


  $('.js-feeds-table').on('keydown', '.js-feed-name-edit', function(e) {

    if(e.keyCode != 13) return

    $.ajax({
      url: '/feed',
      method: 'POST',
      data: {
        _method: 'PATCH',
        feed_id: $(this).data('feed-id'),
        name: $(this).val()
      }
    }).done(function() {
      window.location.reload()
    })
  })


  $('.js-feed-delete').click(function() {
    $.ajax({
      url: '/feed',
      method: 'POST',
      data: {
        _method: 'DELETE',
        feed_id: $(this).data('feed-id')
      }
    }).done(function() {
      window.location.reload()
    })
  })

  $('[data-toggle="tooltip"]').tooltip()

})
