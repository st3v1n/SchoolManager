const pages = document.querySelectorAll('section');
const links = document.querySelectorAll('nav ul li a');
const toggleButton = document.querySelector('.navbar-toggle');
const closeButton = document.querySelector('.navbar-close');
const navBar = document.querySelector('nav');


document.addEventListener('DOMContentLoaded', () => {
    const defaultPage = window.location.hash.substring(1) || pages[0].getAttribute('id');
    showPage(defaultPage);

    links.forEach(link => {
        link.addEventListener('click', (event) => {
            event.preventDefault(); 
            const targetPage = link.getAttribute('href').substring(1);
            showPage(targetPage);
        });
    });

    if (toggleButton && closeButton) {
        toggleButton.addEventListener('click', () => navBar.classList.add('open'));
        closeButton.addEventListener('click', () => navBar.classList.remove('open'));
    }
});

function showPage(targetId) {
    pages.forEach(page => {
        const isVisible = page.getAttribute('id') === targetId;
        page.style.display = isVisible ? 'block' : 'none';
        page.setAttribute('aria-hidden', !isVisible);
    });

    window.location.hash = `#${targetId}`;

    links.forEach(link => {
        if (link.getAttribute('href').substring(1) === targetId) {
            link.classList.add('active');
        } else {
            link.classList.remove('active');
        }
    });
}
