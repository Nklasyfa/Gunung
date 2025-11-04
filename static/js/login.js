document.addEventListener('DOMContentLoaded', function() {
    const loginSection = document.getElementById('login-form-section');
    const registerSection = document.getElementById('register-form-section');
    
    window.showForm = function(formType) {
        loginSection.style.display = formType === 'login' ? 'block' : 'none';
        registerSection.style.display = formType === 'register' ? 'block' : 'none';
    }
    
    const showRegisterElement = document.getElementById('initial-form-data');
    if (showRegisterElement?.dataset.showRegister === 'True') {
        showForm('register');
    }

    // Form validation
    const formRegister = document.getElementById('form-register');
    if (formRegister) {
        formRegister.addEventListener('submit', function(event) {
            const password = this.elements['password'].value;
            if (password.length < 5) {
                event.preventDefault();
                alert('Password harus minimal 5 karakter!');
            }
        });
    }
});