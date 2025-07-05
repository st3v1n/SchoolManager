document.addEventListener('DOMContentLoaded', () => {
    window.popover = document.querySelector('#lepopover');
    window.popoverbackdrop = document.querySelector('.popoverbackdrop');
    const toastElements = document.querySelectorAll('[role="alert"]');


    let popoverTriggersInitialized = false;

    document.addEventListener('htmx:load', function(event){
        if (!popoverTriggersInitialized) {
            document.addEventListener('click', (e) => {
                const trigger = e.target.closest('.popovertrigger');
                if (trigger) {
                    e.preventDefault();
                    popover.classList.toggle('block');
                    popoverbackdrop.classList.toggle('hidden');
                }
            });
            popoverTriggersInitialized = true; // Set the flag to true after first initialization
        }
    });

    // make a global show toast funtion
    window.showToast = function(message, type) {
        toastElements.classList.add('toast', type, 'opacity-0', 'transition-opacity', 'duration-300', 'fixed', 'top-4', 'right-4', 'z-50');
        toast.innerHTML = `<div class="p-4">${message}</div>`;
        document.body.appendChild(toast);
        setTimeout(() => {
            toast.classList.remove('opacity-0');
        }, 10);
    }
    // Close popover if clicking outside of the popover
    popoverbackdrop.addEventListener('click', (e) => {
        if (!popover.contains(e.target)) {
            popover.classList.remove('block');
            popoverbackdrop.classList.add('hidden');
        }
    });

    // Clean up toast elements after a delay
    setTimeout(function() {
        toastElements.forEach(function(toast) {
            toast.classList.add('opacity-0');
            setTimeout(function() {
                toast.remove();
            }, 300);
        });
    }, 5000);

    const indicators = document.querySelectorAll('.htmx-indicator');
    indicators.forEach(indicator => {
        indicator.innerHTML = `<img src="/static/img/indicator.svg" alt="Loading..."/>`;
    });

    function getCookie(name) {
        let cookieValue = null;
        if (document.cookie && document.cookie !== '') {
            const cookies = document.cookie.split(';');
            for (let i = 0; i < cookies.length; i++) {
                const cookie = cookies[i].trim();
                if (cookie.substring(0, name.length + 1) === (name + '=')) {
                    cookieValue = decodeURIComponent(cookie.substring(name.length + 1));
                    break;
                }
            }
        }
        return cookieValue;
    }

    const CsrfToken = getCookie('csrftoken');
});
