document.addEventListener('DOMContentLoaded', () => {
  document.querySelectorAll('input[type="password"]').forEach((input) => {
    const toggle = document.createElement('button');
    toggle.type = 'button';
    toggle.textContent = 'Show password';
    toggle.className = 'password-toggle-btn';

    toggle.addEventListener('click', () => {
      const isHidden = input.type === 'password';
      input.type = isHidden ? 'text' : 'password';
      toggle.textContent = isHidden ? 'Hide password' : 'Show password';
    });

    input.insertAdjacentElement('afterend', toggle);
  });
});
