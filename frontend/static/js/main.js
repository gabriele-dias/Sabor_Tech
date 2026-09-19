document.addEventListener('DOMContentLoaded', () => {
    const form = document.querySelector('.login-form');
    const passwordInput = document.querySelector('#id_password');
    const togglePasswordBtn = document.querySelector('.toggle-password');
    const submitButton = document.querySelector('.login-btn');
    const btnText = submitButton?.querySelector('.btn-text');

    if (togglePasswordBtn && passwordInput) {
        togglePasswordBtn.addEventListener('click', () => {
            const isPassword = passwordInput.type === 'password';
            passwordInput.type = isPassword ? 'text' : 'password';
            togglePasswordBtn.textContent = isPassword ? 'Ocultar' : 'Mostrar';
            togglePasswordBtn.setAttribute('aria-label', isPassword ? 'Ocultar senha' : 'Mostrar senha');
        });
    }

    if (form && submitButton) {
        form.addEventListener('submit', () => {
            submitButton.classList.add('is-loading');
            btnText.textContent = 'Entrando...';
            submitButton.disabled = true;
        });
    }

    const floatingCards = document.querySelectorAll('.feature-card');
    floatingCards.forEach((card, index) => {
        card.style.animationDelay = `${index * 120}ms`;
    });
});
