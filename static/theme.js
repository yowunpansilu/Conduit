document.addEventListener('DOMContentLoaded', () => {
    const toggle = document.getElementById('theme-toggle');
    const icon = document.getElementById('theme-icon');
    const body = document.body;

    // Load saved theme
    if (localStorage.getItem('theme') === 'light') {
        body.classList.add('light-mode');
        if (icon) {
            icon.classList.replace('bi-moon-stars-fill', 'bi-sun-fill');
            icon.classList.remove('text-light');
            icon.classList.add('text-dark');
        }
        if (toggle) {
            toggle.classList.remove('text-light');
            toggle.classList.add('text-dark');
        }
    }

    if (toggle) {
        toggle.addEventListener('click', () => {
            body.classList.toggle('light-mode');
            const isLight = body.classList.contains('light-mode');
            localStorage.setItem('theme', isLight ? 'light' : 'dark');

            if (icon) {
                if (isLight) {
                    icon.classList.replace('bi-moon-stars-fill', 'bi-sun-fill');
                    toggle.classList.remove('text-light');
                    toggle.classList.add('text-dark');
                    icon.classList.remove('text-light');
                    icon.classList.add('text-dark');
                } else {
                    icon.classList.replace('bi-sun-fill', 'bi-moon-stars-fill');
                    toggle.classList.remove('text-dark');
                    toggle.classList.add('text-light');
                    icon.classList.remove('text-dark');
                    icon.classList.add('text-light');
                }
            }
        });
    }
});
