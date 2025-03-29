let editor;

document.addEventListener('DOMContentLoaded', function() {
    const token = localStorage.getItem('token');

    if (!token) {
        window.location.href = '/';
        return;
    }

    function initializeEditor() {
        const sqlEditor = document.getElementById('sql-editor');

        editor = CodeMirror.fromTextArea(sqlEditor, {
            mode: "text/x-sql",
            theme: "eclipse",
            lineNumbers: true,
            indentWithTabs: true,
            tabSize: 4,
            lineWrapping: true,
            matchBrackets: true,
            autofocus: false
        });

        setTimeout(() => editor.refresh(), 10);
    }

    initializeEditor();

    const pathParts = window.location.pathname.split('/');
    const taskId = pathParts[pathParts.length - 1];

    const taskTitle = document.getElementById('task-title');
    const taskDifficulty = document.getElementById('task-difficulty');
    const taskStatus = document.getElementById('task-status');
    const taskDescription = document.getElementById('task-description');
    const schemaInfo = document.getElementById('schema-info');
    const runBtn = document.getElementById('run-btn');
    const submitBtn = document.getElementById('submit-btn');
    const queryError = document.getElementById('query-error');
    const resultsContainer = document.getElementById('results-container');
    const successMessage = document.getElementById('success-message');
    const backToDashboardBtn = document.getElementById('back-to-dashboard');
    const logoutBtn = document.getElementById('logout-btn');

    function getDifficultyInRussian(difficulty) {
        const translations = {
          "Easy": "Легкая",
          "Medium": "Средняя",
          "Hard": "Сложная"
        };
        return translations[difficulty] || difficulty;
    }

    async function loadTaskData() {
        try {
            const response = await fetch(`/api/tasks/${taskId}`, {
                headers: {
                    'Authorization': `Bearer ${token}`
                }
            });

            if (!response.ok) {
                if (response.status === 401) {
                    localStorage.removeItem('token');
                    window.location.href = '/';
                    return;
                }
                throw new Error('Failed to load task');
            }

            const task = await response.json();

            taskTitle.textContent = task.name;
            taskDifficulty.textContent = getDifficultyInRussian(task.difficulty);
            taskDifficulty.className = `task-difficulty ${task.difficulty.toLowerCase()}`;

            if (task.solved) {
                taskStatus.textContent = 'Решена';
                taskStatus.className = 'task-status solved';
            } else {
                taskStatus.textContent = 'Не решена';
                taskStatus.className = 'task-status unsolved';
            }

            taskDescription.textContent = task.description;

            renderSchema(task.schema);
            renderResultSchema(task.result_schema);

        } catch (error) {
            console.error('Error loading task:', error);
            taskDescription.innerHTML = `
                <div class="error">
                    Ошибка при загрузке данных задачи. Попробуй снова или вернись на главную.
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

    function renderSchema(schema) {
        if (!schema || schema.length === 0) {
            schemaInfo.innerHTML = '<div class="no-schema">Нет доступных схем для этой задачи.</div>';
            return;
        }

        let schemaHtml = '';

        schema.forEach(table => {
            schemaHtml += `
                <div class="schema-table">
                    <div class="schema-table-header">
                        <div class="schema-table-name">${table.table_name}</div>
                        <button class="copy-btn copy-tooltip" data-table="${table.table_name}" title="Copy table name">
                            <i class="fas fa-copy"></i>
                            <span class="tooltip-text">Скопировано</span>
                        </button>
                    </div>
                    <div class="schema-table-wrapper">
                        <table class="schema-table-content">
                            <thead>
                                <tr>
                                    <th>Имя колонки</th>
                                    <th>Тип данных</th>
                                    <th>Ограничения</th>
                                </tr>
                            </thead>
                            <tbody>
            `;

            table.columns.forEach(column => {
                schemaHtml += `
                    <tr>
                        <td>${column.name}</td>
                        <td>${column.type}</td>
                        <td>${column.constraints}</td>
                    </tr>
                `;
            });

            schemaHtml += `
                            </tbody>
                        </table>
                    </div>
                </div>
            `;
        });

        schemaInfo.innerHTML = schemaHtml;

        document.querySelectorAll('.copy-btn').forEach(button => {
            button.addEventListener('click', function() {
                const tableName = this.getAttribute('data-table');
                copyTextToClipboard(tableName, this);
            });
        });
    }

    function copyTextToClipboard(text, buttonElement) {
        const textArea = document.createElement("textarea");
        textArea.value = text;
        textArea.style.position = "fixed";
        document.body.appendChild(textArea);
        textArea.focus();
        textArea.select();

        try {
            const successful = document.execCommand('copy');

            if (successful) {
                buttonElement.classList.add('show-tooltip');

                setTimeout(() => {
                    buttonElement.classList.remove('show-tooltip');
                }, 1500);
            }
        } catch (err) {
            console.error('Unable to copy', err);
        }

        document.body.removeChild(textArea);
    }

    function renderResultSchema(resultSchema) {
        const resultSchemaInfo = document.getElementById('result-schema-info');

        if (!resultSchema || resultSchema.length === 0) {
            resultSchemaInfo.innerHTML = '<div class="no-schema">Нет схемы результата для этой задачи.</div>';
            return;
        }

        let schemaHtml = `
            <div class="schema-table">
                <div class="schema-table-wrapper">
                    <table class="schema-table-content">
                        <thead>
                            <tr>
                                <th>Имя колонки</th>
                                <th>Тип данных</th>
                                <th>Описание</th>
                            </tr>
                        </thead>
                        <tbody>
        `;

        resultSchema.forEach(column => {
            schemaHtml += `
                <tr>
                    <td><strong>${column.name}</strong></td>
                    <td>${column.type}</td>
                    <td class="column-description">${column.description}</td>
                </tr>
            `;
        });

        schemaHtml += `
                        </tbody>
                    </table>
                </div>
            </div>
        `;

        resultSchemaInfo.innerHTML = schemaHtml;
    }

    async function runQuery() {
        const query = editor.getValue().trim();

        if (!query) {
            queryError.textContent = 'Запрос не может быть пустым.';
            return;
        }

        queryError.textContent = '';
        resultsContainer.innerHTML = '<div class="loading">Запрос выполняется...</div>';

        try {
            const response = await fetch(`/api/tasks/${taskId}/run`, {
                method: 'POST',
                headers: {
                    'Authorization': `Bearer ${token}`,
                    'Content-Type': 'application/json'
                },
                body: JSON.stringify({
                    query: query
                })
            });

            const data = await response.json();

            if (!response.ok || !data.success) {
                throw new Error(data.error || 'Failed to run query');
            }

            renderQueryResults(data.results);

        } catch (error) {
            queryError.textContent = error.message;
            resultsContainer.innerHTML = '<div class="no-results">Ошибка при выполнении запроса.</div>';
        }
    }


    function renderQueryResults(results) {
        if (!results || results.length === 0) {
            resultsContainer.innerHTML = '<div class="no-results">Запрос ничего не вернул.</div>';
            return;
        }

        const columns = Object.keys(results[0]);

        let tableHtml = `
            <table class="results-table">
                <thead>
                    <tr>
                        ${columns.map(col => `<th>${col}</th>`).join('')}
                    </tr>
                </thead>
                <tbody>
        `;

        results.forEach(row => {
            tableHtml += '<tr>';
            columns.forEach(col => {
                const value = row[col] === null ? 'NULL' : row[col];
                tableHtml += `<td>${value}</td>`;
            });
            tableHtml += '</tr>';
        });

        tableHtml += `
                </tbody>
            </table>
        `;

        resultsContainer.innerHTML = tableHtml;
    }

    async function submitSolution() {
        const query = editor.getValue().trim();

        if (!query) {
            queryError.textContent = 'Запрос не может быть пустым.';
            return;
        }

        queryError.textContent = '';

        try {
            const response = await fetch(`/api/tasks/${taskId}/submit`, {
                method: 'POST',
                headers: {
                    'Authorization': `Bearer ${token}`,
                    'Content-Type': 'application/json'
                },
                body: JSON.stringify({
                    query: query
                })
            });

            const data = await response.json();

            if (!response.ok) {
                throw new Error('Failed to submit solution');
            }

            if (data.success) {
                successMessage.classList.remove('hidden');

                taskStatus.textContent = 'Solved';
                taskStatus.className = 'task-status solved';
            } else {
                queryError.textContent = data.message || 'Решение неверно.';
            }

        } catch (error) {
            queryError.textContent = error.message;
        }
    }


    runBtn.addEventListener('click', runQuery);
    submitBtn.addEventListener('click', submitSolution);

    backToDashboardBtn.addEventListener('click', () => {
        window.location.href = '/dashboard';
    });

    logoutBtn.addEventListener('click', () => {
        localStorage.removeItem('token');
        window.location.href = '/';
    });

    loadUserInfo();
    loadTaskData();
});
