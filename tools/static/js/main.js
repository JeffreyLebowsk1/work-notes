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

// Hamburger menu toggle for tablet/medium screens.
(function () {
    var btn = document.getElementById('nav-hamburger');
    var drawer = document.getElementById('nav-drawer');
    if (!btn || !drawer) return;

    btn.addEventListener('click', function () {
        var open = btn.classList.toggle('open');
        drawer.classList.toggle('open', open);
        btn.setAttribute('aria-expanded', String(open));
    });

    // Close drawer when a link inside it is clicked.
    drawer.querySelectorAll('a').forEach(function (link) {
        link.addEventListener('click', function () {
            btn.classList.remove('open');
            drawer.classList.remove('open');
            btn.setAttribute('aria-expanded', 'false');
        });
    });

    // Close drawer on Escape key.
    document.addEventListener('keydown', function (e) {
        if (e.key === 'Escape' && drawer.classList.contains('open')) {
            btn.classList.remove('open');
            drawer.classList.remove('open');
            btn.setAttribute('aria-expanded', 'false');
        }
    });
}());
