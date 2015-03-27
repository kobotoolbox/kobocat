$(document).ready(function() {
  $(document).on("click", ".header-bar__top-level-menu-button", function () {
    $('.top-level-menu').toggleClass('is-active');
  });

  $('table.published_forms__table').footable();
}); 
