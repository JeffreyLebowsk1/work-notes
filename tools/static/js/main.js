// CCCC Notes — main.js

// Highlight the active bottom-nav item based on the current URL path.
(function () {
    var path = window.location.pathname;
    document.querySelectorAll('.bottom-nav-item').forEach(function (el) {
        var href = el.getAttribute('data-path') || el.getAttribute('href');
        if (!href) return;
        var active = href === '/' ? path === '/' : path.startsWith(href);
        if (active) el.classList.add('active');
    });
}());
