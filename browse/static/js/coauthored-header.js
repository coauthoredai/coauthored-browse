// Coauthored header: the search overlay toggle and the phone menu. Works without JS too:
// the search link goes to /search and the menu is shown.
document.addEventListener("DOMContentLoaded", function () {
  var searchToggle = document.getElementById("ds-search-toggle");
  var overlay = document.getElementById("ds-search-overlay");
  if (searchToggle && overlay) {
    searchToggle.addEventListener("click", function (e) {
      e.preventDefault();
      var open = overlay.hidden;
      overlay.hidden = !open;
      searchToggle.setAttribute("aria-expanded", String(open));
      if (open) { var input = document.getElementById("ds-search-input"); if (input) input.focus(); }
    });
  }
  var navToggle = document.getElementById("ds-nav-toggle");
  var nav = document.getElementById("ds-site-header-nav");
  if (navToggle && nav) {
    navToggle.addEventListener("click", function () {
      var open = !nav.classList.contains("is-open");
      nav.classList.toggle("is-open", open);
      navToggle.setAttribute("aria-expanded", String(open));
      navToggle.setAttribute("aria-label", open ? "Close menu" : "Open menu");
    });
  }
});
