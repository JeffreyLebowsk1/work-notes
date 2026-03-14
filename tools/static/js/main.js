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

// Dark mode toggle — persists choice in localStorage, defaults to light.
(function () {
    var STORAGE_KEY = 'cccc-theme';
    var btn = document.getElementById('theme-toggle');
    if (!btn) return;

    function applyTheme(theme) {
        document.documentElement.setAttribute('data-theme', theme);
        btn.textContent = theme === 'dark' ? '☀️' : '🌙';
        btn.title = theme === 'dark' ? 'Switch to light mode' : 'Switch to dark mode';
        // Update theme-color meta for mobile browser chrome
        var meta = document.querySelector('meta[name="theme-color"]');
        if (meta) meta.setAttribute('content', theme === 'dark' ? '#0d1117' : '#1d3557');
    }

    var saved = localStorage.getItem(STORAGE_KEY) || 'light';
    applyTheme(saved);

    btn.addEventListener('click', function () {
        var next = document.documentElement.getAttribute('data-theme') === 'dark' ? 'light' : 'dark';
        localStorage.setItem(STORAGE_KEY, next);
        applyTheme(next);
    });
}());
