let themeToggle = null;
try {
  themeToggle = document.getElementById('theme-icon');
  const currentTheme = localStorage.getItem('theme') || 'dark';

  if (currentTheme === 'light') {
    document.body.classList.add('light-mode');
    if (themeToggle && themeToggle.classList) {
      themeToggle.classList.remove('fa-moon');
      themeToggle.classList.add('fa-sun');
    }
  }

  function toggleTheme() {
    document.body.classList.toggle('light-mode');
    const isLightMode = document.body.classList.contains('light-mode');

    if (themeToggle && themeToggle.classList) {
      if (isLightMode) {
        themeToggle.classList.remove('fa-moon');
        themeToggle.classList.add('fa-sun');
        localStorage.setItem('theme', 'light');
      } else {
        themeToggle.classList.remove('fa-sun');
        themeToggle.classList.add('fa-moon');
        localStorage.setItem('theme', 'dark');
      }
    } else {
      // still persist theme choice even if icon isn't present
      localStorage.setItem('theme', isLightMode ? 'light' : 'dark');
    }
  }
} catch (e) {
  // Defensive: prevent any DOM-related error from stopping script execution
  console.warn('theme toggle init failed', e);
  function toggleTheme() {
    const isLight = document.body.classList.toggle('light-mode');
    localStorage.setItem('theme', isLight ? 'light' : 'dark');
  }
}

    /**
     * Handle Newsletter Subscription
     * Sends email to API endpoint for newsletter subscription
     */
    function handleNewsletterSubmit(event) {
      event.preventDefault();
      
      const form = event.target;
      const emailInput = form.querySelector('input[type="email"]');
      const email = emailInput.value.trim();
      const submitBtn = form.querySelector('button[type="submit"]');
      
      // Disable button during submission
      submitBtn.disabled = true;
      const originalText = submitBtn.textContent;
      submitBtn.textContent = 'Subscribing...';
      
      // Send subscription request
      fetch('/api/newsletter/subscribe/', {
        method: 'POST',
        headers: {
          'Content-Type': 'application/json',
          'X-CSRFToken': getCookie('csrftoken')
        },
        body: JSON.stringify({ email: email })
      })
      .then(response => response.json())
      .then(data => {
        if (data.success) {
          // Show success message
          showNotification('success', data.message);
          emailInput.value = '';
        } else {
          showNotification('error', data.message);
        }
      })
      .catch(error => {
        console.error('Error:', error);
        showNotification('error', 'An error occurred while subscribing. Please try again.');
      })
      .finally(() => {
        // Re-enable button
        submitBtn.disabled = false;
        submitBtn.textContent = originalText;
      });
    }

    /**
     * Get CSRF token from cookies
     */
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

    /**
     * Show notification message
     */
    function showNotification(type, message) {
      // Create notification container if it doesn't exist
      let notifContainer = document.getElementById('notification-container');
      if (!notifContainer) {
        notifContainer = document.createElement('div');
        notifContainer.id = 'notification-container';
        notifContainer.style.cssText = `
          position: fixed;
          top: 20px;
          right: 20px;
          z-index: 9999;
          max-width: 400px;
        `;
        document.body.appendChild(notifContainer);
      }
      
      // Create notification element
      const notif = document.createElement('div');
      notif.style.cssText = `
        padding: 1rem;
        margin-bottom: 10px;
        border-radius: 8px;
        font-weight: 500;
        animation: slideIn 0.3s ease-in-out;
        background: ${type === 'success' ? '#d4edda' : '#f8d7da'};
        color: ${type === 'success' ? '#155724' : '#721c24'};
        border: 1px solid ${type === 'success' ? '#c3e6cb' : '#f5c6cb'};
      `;
      notif.textContent = message;
      
      notifContainer.appendChild(notif);
      
      // Remove notification after 5 seconds
      setTimeout(() => {
        notif.style.animation = 'slideOut 0.3s ease-in-out';
        setTimeout(() => notif.remove(), 300);
      }, 5000);
    }

    // Add CSS animations
    const style = document.createElement('style');
    style.textContent = `
      @keyframes slideIn {
        from { transform: translateX(400px); opacity: 0; }
        to { transform: translateX(0); opacity: 1; }
      }
      @keyframes slideOut {
        from { transform: translateX(0); opacity: 1; }
        to { transform: translateX(400px); opacity: 0; }
      }
    `;
    document.head.appendChild(style);
document.addEventListener('DOMContentLoaded', () => {
  const hamburger = document.querySelector('.hamburger');
  const navLinks = document.querySelector('.nav-links');

  if (!hamburger || !navLinks) return;

  // Toggle nav visibility and animate the hamburger
  hamburger.addEventListener('click', (e) => {
    console.debug && console.debug('hamburger clicked');
    e.stopPropagation();
    const isOpen = navLinks.classList.toggle('active');
    hamburger.classList.toggle('open', isOpen);
    // set aria-expanded for accessibility
    const expanded = hamburger.getAttribute('aria-expanded') === 'true';
    hamburger.setAttribute('aria-expanded', String(!expanded));
  });

  // Close menu when clicking outside
  document.addEventListener('click', (ev) => {
    if (!navLinks.classList.contains('active')) return;
    if (!ev.target.closest('.nav-links') && !ev.target.closest('.hamburger')) {
      navLinks.classList.remove('active');
      hamburger.classList.remove('open');
      hamburger.setAttribute('aria-expanded', 'false');
    }
  });
});
