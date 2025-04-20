document.addEventListener('DOMContentLoaded', function() {
    const token = localStorage.getItem('token');

    if (!token) {
        window.location.href = '/';
        return;
    }

    const tablesContainer = document.getElementById('tables-container');
    const schemaView = document.getElementById('schema-view');
    const resultsContainer = document.getElementById('results-container');
    const queryError = document.getElementById('query-error');
    const runQueryBtn = document.getElementById('run-query-btn');
    const clearQueryBtn = document.getElementById('clear-query-btn');
    const saveTaskBtn = document.getElementById('save-task-btn');
    const cancelBtn = document.getElementById('cancel-btn');
    const addResultColumnBtn = document.getElementById('add-result-column');
    const resultColumnsContainer = document.getElementById('result-columns-container');
    const notificationElement = document.getElementById('notification');

    let availableTables = [];
    let selectedTables = [];
    let resultColumns = [];
    let editor;

    initializeEditor();

    loadAdminPageData();

    function initializeEditor() {
        const sqlEditor = document.getElementById('solution-query');

        editor = CodeMirror.fromTextArea(sqlEditor, {
            mode: "text/x-sql",
            theme: "eclipse",
            lineNumbers: true,
            indentWithTabs: false,
            indentUnit: 2,
            tabSize: 2,
            smartIndent: true,
            lineWrapping: true,
            matchBrackets: true,
            autoCloseBrackets: true,
            styleActiveLine: true,
            foldGutter: true,
            gutters: ["CodeMirror-linenumbers", "CodeMirror-foldgutter"],

            extraKeys: {
                "Tab": function(cm) {
                    if (cm.somethingSelected()) {
                        cm.indentSelection("add");
                    } else {
                        cm.replaceSelection("  ", "end");
                    }
                },
                "Shift-Tab": function(cm) {
                    cm.indentSelection("subtract");
                },
                "Ctrl-/": "toggleComment",
                "Cmd-/": "toggleComment",
                "Enter": function(cm) {
                    const cursor = cm.getCursor();
                    const line = cm.getLine(cursor.line);

                    const indentation = line.match(/^\s*/)[0];

                    const openParenMatch = line.match(/.*\(\s*$/);

                    const keywordMatch = line.match(/\b(SELECT|FROM|WHERE|GROUP BY|ORDER BY|HAVING|JOIN)\b.*$/i);

                    if (openParenMatch) {
                        cm.replaceSelection("\n" + indentation + "  ");
                        return;
                    } else if (keywordMatch) {
                        cm.replaceSelection("\n" + indentation + "  ");
                        return;
                    }

                    cm.replaceSelection("\n" + indentation);
                }
            },

            autoCloseBrackets: {
                pairs: '()[]{}\'\'""',
                triples: '',
                explode: '{}',
                override: true
            }
        });

        setTimeout(() => editor.refresh(), 10);
    }

    async function loadAdminPageData() {
        try {
            const userResponse = await fetch('/api/user/current', {
                headers: {
                    'Authorization': `Bearer ${token}`
                }
            });

            if (!userResponse.ok) {
                throw new Error('Failed to load user info');
            }

            const userData = await userResponse.json();
            document.getElementById('username').textContent = userData.username;

            if (!userData.is_admin) {
                window.location.href = '/dashboard';
                return;
            }

            const tablesResponse = await fetch('/api/admin/tables', {
                headers: {
                    'Authorization': `Bearer ${token}`
                }
            });

            if (!tablesResponse.ok) {
                throw new Error('Failed to load tables');
            }

            availableTables = await tablesResponse.json();
            renderAvailableTables();

        } catch (error) {
            console.error('Error loading admin page data:', error);
            showNotification('Ошибка при загрузке страницы. Пожалуйста попробуйте снова', 'error');
        }
    }

    function renderAvailableTables() {
        if (!availableTables.length) {
            tablesContainer.innerHTML = '<div class="no-tables">Нет доступных таблиц</div>';
            return;
        }

        const tableItems = availableTables.map(table => `
            <div class="table-item" data-table="${table.name}">
                ${table.name}
            </div>
        `).join('');

        tablesContainer.innerHTML = tableItems;

        document.querySelectorAll('.table-item').forEach(item => {
            item.addEventListener('click', () => {
                const tableName = item.getAttribute('data-table');
                toggleTableSelection(tableName, item);
            });
        });
    }

    function toggleTableSelection(tableName, element) {
        if (selectedTables.includes(tableName)) {
            selectedTables = selectedTables.filter(name => name !== tableName);
            element.classList.remove('selected');
        } else {
            selectedTables.push(tableName);
            element.classList.add('selected');
        }

        updateSchemaView();
    }

    function updateSchemaView() {
        if (!selectedTables.length) {
            schemaView.innerHTML = '<div class="loading">Выбери таблицу, чтобы увидеть их схему</div>';
            return;
        }

        let schemaHtml = '';

        const selectedTablesData = availableTables.filter(table =>
            selectedTables.includes(table.name)
        );

        selectedTablesData.forEach(table => {
            schemaHtml += `
                <div class="schema-table">
                    <div class="schema-heading">${table.name}</div>
                    <div class="schema-columns">
            `;

            table.columns.forEach(column => {
                schemaHtml += `
                    <div class="column-item">
                        ${column.name} (${column.type}) ${column.constraints ? column.constraints : ''}
                    </div>
                `;
            });

            schemaHtml += `
                    </div>
                </div>
            `;
        });

        schemaView.innerHTML = schemaHtml;
    }

    function addResultColumn() {
        const columnId = Date.now();
        const columnRow = document.createElement('div');
        columnRow.className = 'result-column-row';
        columnRow.setAttribute('data-id', columnId);

        columnRow.innerHTML = `
            <div style="display: flex; gap: 1rem; margin-bottom: 0.5rem;">
                <input type="text" placeholder="Имя колонки" class="column-name" style="flex: 1;">
                <input type="text" placeholder="Тип данных" class="column-type" style="flex: 1;">
                <input type="text" placeholder="Описание" class="column-description" style="flex: 2;">
                <button data-id="${columnId}" class="btn remove-column">
                    <i class="fas fa-times"></i>
                </button>
            </div>
        `;

        resultColumnsContainer.insertBefore(columnRow, addResultColumnBtn);

        columnRow.querySelector('.remove-column').addEventListener('click', function() {
            columnRow.remove();
        });
    }

    function getResultSchema() {
        const columns = [];
        document.querySelectorAll('.result-column-row').forEach(row => {
            const nameInput = row.querySelector('.column-name');
            const typeInput = row.querySelector('.column-type');
            const descriptionInput = row.querySelector('.column-description');

            if (nameInput.value.trim() && typeInput.value.trim()) {
                columns.push({
                    name: nameInput.value.trim(),
                    type: typeInput.value.trim(),
                    description: descriptionInput.value.trim() || ''
                });
            }
        });

        return columns;
    }

    async function runQuery() {
        const query = editor.getValue().trim();

        if (!query) {
            queryError.textContent = 'Запрос не может быть пустым';
            return;
        }

        if (!selectedTables.length) {
            queryError.textContent = 'Хотя бы одна таблица должна быть выбрана';
            return;
        }

        queryError.textContent = '';
        resultsContainer.innerHTML = '<div class="loading">Запрос выполняется...</div>';

        try {
            const response = await fetch('/api/admin/run-query', {
                method: 'POST',
                headers: {
                    'Authorization': `Bearer ${token}`,
                    'Content-Type': 'application/json'
                },
                body: JSON.stringify({
                    query: query,
                    tables: selectedTables
                })
            });

            const data = await response.json();

            if (!response.ok || !data.success) {
                throw new Error(data.error || 'Failed to run query');
            }

            renderQueryResults(data.results);

        } catch (error) {
            queryError.textContent = error.message;
            resultsContainer.innerHTML = '<div class="no-results">Ошибка при выполнении запроса</div>';
        }
    }

    function renderQueryResults(results) {
        if (!results || results.length === 0) {
            resultsContainer.innerHTML = '<div class="no-results">Запрос ничего не вернул</div>';
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

    function clearQuery() {
        editor.setValue('');
        editor.focus();
    }

    async function saveTask() {
        const taskName = document.getElementById('task-name').value.trim();
        const taskDifficulty = document.getElementById('task-difficulty').value;
        const taskDescription = document.getElementById('task-description').value.trim();
        const solutionQuery = editor.getValue().trim();
        const resultSchema = getResultSchema();

        if (!taskName) {
            showNotification('Название задачи обязательно', 'error');
            return;
        }

        if (!taskDescription) {
            showNotification('Условие задачи обязательно', 'error');
            return;
        }

        if (!selectedTables.length) {
            showNotification('Должна быть выбрана хотя бы одна таблица', 'error');
            return;
        }

        if (!solutionQuery) {
            showNotification('Решение обязательно', 'error');
            return;
        }

        if (!resultSchema.length) {
            showNotification('Схема результата обязательна', 'error');
            return;
        }

        try {
            const response = await fetch('/api/admin/tasks', {
                method: 'POST',
                headers: {
                    'Authorization': `Bearer ${token}`,
                    'Content-Type': 'application/json'
                },
                body: JSON.stringify({
                    name: taskName,
                    description: taskDescription,
                    difficulty: taskDifficulty,
                    solution_query: solutionQuery,
                    tables: selectedTables,
                    result_schema: resultSchema
                })
            });

            const data = await response.json();

            if (!response.ok) {
                throw new Error(data.detail || 'Failed to create task');
            }

            showNotification('Задача успешно добавлена!', 'success');

            setTimeout(() => {
                window.location.href = '/dashboard';
            }, 500);

        } catch (error) {
            console.error('Error saving task:', error);
            showNotification(error.message, 'error');
        }
    }

    function showNotification(message, type) {
        notificationElement.textContent = message;
        notificationElement.className = `notification ${type}`;
        notificationElement.classList.add('show');

        setTimeout(() => {
            notificationElement.classList.remove('show');
        }, 3000);
    }

    runQueryBtn.addEventListener('click', runQuery);
    clearQueryBtn.addEventListener('click', clearQuery);
    saveTaskBtn.addEventListener('click', saveTask);
    cancelBtn.addEventListener('click', () => window.location.href = '/dashboard');
    addResultColumnBtn.addEventListener('click', addResultColumn);

    document.getElementById('logout-btn').addEventListener('click', () => {
        localStorage.removeItem('token');
        window.location.href = '/';
    });

    addResultColumn();
});
