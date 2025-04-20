document.addEventListener('DOMContentLoaded', function() {
    const token = localStorage.getItem('token');
    if (token) {
        window.location.href = '/dashboard';
    }

    const loginTab = document.getElementById('login-tab');
    const registerTab = document.getElementById('register-tab');
    const loginForm = document.getElementById('login-form');
    const registerForm = document.getElementById('register-form');

    loginTab.addEventListener('click', function() {
        loginTab.classList.add('active');
        registerTab.classList.remove('active');
        loginForm.classList.remove('hidden');
        registerForm.classList.add('hidden');
    });

    registerTab.addEventListener('click', function() {
        registerTab.classList.add('active');
        loginTab.classList.remove('active');
        registerForm.classList.remove('hidden');
        loginForm.classList.add('hidden');
    });

    const loginFormElement = document.getElementById('login');
    const loginError = document.getElementById('login-error');

    loginFormElement.addEventListener('submit', async function(e) {
        e.preventDefault();

        const username = document.getElementById('login-username').value;
        const password = document.getElementById('login-password').value;

        if (!username || !password) {
            loginError.textContent = 'Пожалуйста, заполни все поля';
            return;
        }

        try {
            const formData = new FormData();
            formData.append('username', username);
            formData.append('password', password);

            const response = await fetch('/api/login', {
                method: 'POST',
                body: formData
            });

            const data = await response.json();

            if (!response.ok) {
                throw new Error(data.detail || 'Login failed');
            }

            localStorage.setItem('token', data.access_token);
            window.location.href = '/dashboard';
        } catch (error) {
            loginError.textContent = error.message;
        }
    });

    const registerFormElement = document.getElementById('register');
    const registerError = document.getElementById('register-error');

    registerFormElement.addEventListener('submit', async function(e) {
        e.preventDefault();

        const username = document.getElementById('reg-username').value;
        const email = document.getElementById('reg-email').value;
        const password = document.getElementById('reg-password').value;
        const confirmPassword = document.getElementById('reg-confirm-password').value;
        const secretKey = document.getElementById('reg-secret-key').value;

        if (!username || !email || !password || !confirmPassword) {
            registerError.textContent = 'Пожалуйста, заполни все поля';
            return;
        }

        if (password !== confirmPassword) {
            registerError.textContent = 'Пароли не совпадают';
            return;
        }

        try {
            const response = await fetch('/api/register', {
                method: 'POST',
                headers: {
                    'Content-Type': 'application/json'
                },
                body: JSON.stringify({
                    username,
                    email,
                    password,
                    secret_key: secretKey
                })
            });

            const data = await response.json();

            if (!response.ok) {
                throw new Error(data.detail || 'Не удалось выполнить регистрацию');
            }

            registerError.textContent = '';
            registerError.innerHTML = '<span style="color: green">Регистрация успешна! Теперь ты можешь войти.</span>';

            const registeredUsername = username;

            registerFormElement.reset();

            setTimeout(() => {
                loginTab.click();
                document.getElementById('login-username').value = registeredUsername;
                document.getElementById('login-password').focus();
            }, 500);
        } catch (error) {
            registerError.textContent = error.message;
        }
    });
});
