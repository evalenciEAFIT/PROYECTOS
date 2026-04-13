document.addEventListener('DOMContentLoaded', () => {
    let currentZoom = parseInt(localStorage.getItem('wcag-zoom')) || 100;
    let highContrast = localStorage.getItem('wcag-contrast') === 'true';

    const applyZoom = () => {
        document.documentElement.style.fontSize = currentZoom + '%';
        localStorage.setItem('wcag-zoom', currentZoom);
    };

    const applyContrast = () => {
        if (highContrast) {
            document.body.classList.add('high-contrast-mode');
        } else {
            document.body.classList.remove('high-contrast-mode');
        }
        localStorage.setItem('wcag-contrast', highContrast);
    };

    // Apply on load
    applyZoom();
    applyContrast();

    // Delegate events because Dash components render after DOMContentLoaded
    document.body.addEventListener('click', (e) => {
        const target = e.target.closest('button');
        if (!target) return;

        if (target.id === 'wcag-increase') {
            if (currentZoom < 150) { // Max 150%
                currentZoom += 10;
                applyZoom();
            }
        }
        if (target.id === 'wcag-decrease') {
            if (currentZoom > 70) { // Min 70%
                currentZoom -= 10;
                applyZoom();
            }
        }
        if (target.id === 'wcag-contrast') {
            highContrast = !highContrast;
            applyContrast();
        }
    });
});
