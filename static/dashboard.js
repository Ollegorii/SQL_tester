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
                    Failed to load data. Please try again or log out and back in.
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
            tasksListElement.innerHTML = '<div class="loading">No tasks match your filters</div>';
            return;
        }

        const taskHtml = filteredTasks.map(task => `
            <div class="task-item" data-id="${task.id}">
                <div class="task-info">
                    <div class="task-number">${task.id}</div>
                    <a href="/task/${task.id}" class="task-name">${task.name}</a>
                    <div class="task-difficulty ${task.difficulty.toLowerCase()}">${task.difficulty}</div>
                </div>
                <div class="task-status ${task.solved ? 'solved' : 'unsolved'}">
                    ${task.solved ?
                        '<span>✓ Solved</span>' :
                        '<span>Unsolved</span>'
                    }
                </div>
            </div>
        `).join('');

        tasksListElement.innerHTML = taskHtml;

        document.querySelectorAll('.task-item').forEach(item => {
            item.addEventListener('click', (e) => {
                if (!e.target.classList.contains('task-name')) {
                    const taskId = item.getAttribute('data-id');
                    window.location.href = `/task/${taskId}`;
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

    loadUserInfo();
    loadDashboard();
});
