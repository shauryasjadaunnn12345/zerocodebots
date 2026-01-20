

    document.addEventListener('DOMContentLoaded', function () {
      const passwordInputs = document.querySelectorAll('form input[type="password"]');
      passwordInputs.forEach(function (input) {
        const toggle = document.createElement('button');
        toggle.type = 'button';
        toggle.textContent = 'Show password';
        toggle.className = 'password-toggle-btn';

        toggle.addEventListener('click', function () {
          if (input.type === 'password') {
            input.type = 'text';
            toggle.textContent = 'Hide password';
          } else {
            input.type = 'password';
            toggle.textContent = 'Show password';
          }
        });

        if (input.parentElement) {
          input.parentElement.appendChild(toggle);
        } else {
          input.insertAdjacentElement('afterend', toggle);
        }
      });
    });
