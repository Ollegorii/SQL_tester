document.addEventListener('DOMContentLoaded', function() {
    const token = localStorage.getItem('token');

    if (!token) {
        window.location.href = '/';
        return;
    }

    const tasksListElement = document.getElementById('tasks-list');
    const difficultyFilter = document.getElementById('difficulty-filter');
    const statusFilter = document.getElementById('status-filter');
    const logoutBtn = document.getElementById('logout-btn');

    let allTasks = [];

    async function loadDashboard() {
        try {
            const tasksResponse = await fetch('/api/tasks', {
                headers: {
                    'Authorization': `Bearer ${token}`
                }
            });

            if (!tasksResponse.ok) {
                if (tasksResponse.status === 401) {
                    localStorage.removeItem('token');
                    window.location.href = '/';
                    return;
                }
                throw new Error('Failed to load tasks');
            }

            allTasks = await tasksResponse.json();
            renderTasks(allTasks);

            const statsResponse = await fetch('/api/user/stats', {
                headers: {
                    'Authorization': `Bearer ${token}`
                }
            });

            if (!statsResponse.ok) {
                throw new Error('Failed to load user stats');
            }

            const stats = await statsResponse.json();
            updateStats(stats);

        } catch (error) {
            console.error('Error loading dashboard:', error);
            tasksListElement.innerHTML = `
                <div class="error">
                    Ошибка при загрузке данных. Пожалуйста, повторите попытку
                </div>
            `;
        }
    }

    async function loadUserInfo() {
        try {
            const response = await fetch('/api/user/current', {
                headers: {
                    'Authorization': `Bearer ${token}`
                }
            });

            if (!response.ok) {
                throw new Error('Failed to load user info');
            }

            const user = await response.json();
            document.getElementById('username').textContent = user.username;
        } catch (error) {
            console.error('Error loading user info:', error);
            document.getElementById('username').textContent = 'User';
        }
    }

    function renderTasks(tasks) {
        const difficulty = difficultyFilter.value;
        const status = statusFilter.value;

        let filteredTasks = tasks;

        if (difficulty !== 'all') {
            filteredTasks = filteredTasks.filter(task => task.difficulty === difficulty);
        }

        if (status === 'solved') {
            filteredTasks = filteredTasks.filter(task => task.solved);
        } else if (status === 'unsolved') {
            filteredTasks = filteredTasks.filter(task => !task.solved);
        }

        if (filteredTasks.length === 0) {
            tasksListElement.innerHTML = '<div class="loading">Нет задач, подходящих под фильтры</div>';
            return;
        }

        tasksListElement.innerHTML = '<div class="tasks-grid" id="tasks-grid"></div>';
        const tasksGrid = document.getElementById('tasks-grid');

        filteredTasks.forEach(task => {
            const taskCard = document.createElement('div');
            taskCard.className = 'task-card';
            taskCard.setAttribute('data-id', task.id);

            taskCard.innerHTML = `
                <div class="task-card-header">
                    <div class="task-id">Задача #${task.id}</div>
                    <a href="/task/${task.id}" class="task-card-title">${task.name}</a>
                </div>
                <div class="task-card-footer">
                    <div class="task-difficulty ${task.difficulty.toLowerCase()}">${task.difficulty}</div>
                    <div class="task-card-status ${task.solved ? 'solved' : 'unsolved'}">
                        ${task.solved ? '✓ Решена' : 'Не решена'}
                    </div>
                </div>
            `;

            tasksGrid.appendChild(taskCard);

            taskCard.addEventListener('click', (e) => {
                if (!e.target.classList.contains('task-card-title')) {
                    window.location.href = `/task/${task.id}`;
                }
            });
        });
    }

    function updateStats(stats) {
        document.getElementById('solved-count').textContent = stats.solved_count;
        document.getElementById('total-count').textContent = stats.total_count;
        document.getElementById('completion-percentage').textContent = `${stats.completion_percentage}%`;

        const progressBar = document.querySelector('.progress');
        progressBar.style.width = `${stats.completion_percentage}%`;
    }

    difficultyFilter.addEventListener('change', () => {
        renderTasks(allTasks);
    });

    statusFilter.addEventListener('change', () => {
        renderTasks(allTasks);
    });

    logoutBtn.addEventListener('click', () => {
        localStorage.removeItem('token');
        window.location.href = '/';
    });

    const clearFiltersBtn = document.getElementById('clear-filters-btn');

    clearFiltersBtn.addEventListener('click', () => {
        difficultyFilter.value = 'all';
        statusFilter.value = 'all';
        renderTasks(allTasks);
    });

    loadUserInfo();
    loadDashboard();
});
