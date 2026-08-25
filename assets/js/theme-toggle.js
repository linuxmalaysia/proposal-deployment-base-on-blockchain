// Theme Toggle JS for Laboratory Template
document.addEventListener('DOMContentLoaded', function() {
  const themeButtons = document.querySelectorAll('[data-theme-set]');
  const html = document.documentElement;

  function setTheme(theme) {
    if (theme === 'auto') {
      const prefersDark = window.matchMedia('(prefers-color-scheme: dark)').matches;
      html.setAttribute('data-theme', prefersDark ? 'dark' : 'light');
    } else {
      html.setAttribute('data-theme', theme);
    }
    localStorage.setItem('dca_theme', theme);

    themeButtons.forEach(btn => {
      if (btn.getAttribute('data-theme-set') === theme) {
        btn.classList.add('active');
      } else {
        btn.classList.remove('active');
      }
    });
  }

  const savedTheme = localStorage.getItem('dca_theme') || 'auto';
  setTheme(savedTheme);

  themeButtons.forEach(btn => {
    btn.addEventListener('click', function() {
      const mode = this.getAttribute('data-theme-set');
      setTheme(mode);
    });
  });
});
