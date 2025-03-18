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
            loginError.textContent = 'Please fill in all fields';
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

        if (!username || !email || !password || !confirmPassword) {
            registerError.textContent = 'Please fill in all fields';
            return;
        }

        if (password !== confirmPassword) {
            registerError.textContent = 'Passwords do not match';
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
                    password
                })
            });

            const data = await response.json();

            if (!response.ok) {
                throw new Error(data.detail || 'Registration failed');
            }

            registerError.textContent = '';
            registerError.innerHTML = '<span style="color: green">Registration successful! You can now login.</span>';

            const registeredUsername = username;

            registerFormElement.reset();

            setTimeout(() => {
                loginTab.click();
                document.getElementById('login-username').value = registeredUsername;
                document.getElementById('login-password').focus();
            }, 1500);
        } catch (error) {
            registerError.textContent = error.message;
        }
    });
});
