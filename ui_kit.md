# Документация UI Kit

Здесь содержится детальное описание всех UI-компоненты на различных страницах приложения SQL Tester, включая их спецификации по размеру, цветам и шрифтам.

## Содержание
1. [Цветовая палитра](#цветовая-палитра)
2. [Типографика](#типографика)
3. [Общие компоненты](#общие-компоненты)
4. [Страница входа/регистрации](#страница-входарегистрации)
5. [Страница дашборда](#страница-дашборда)
6. [Страница с деталями задания](#страница-с-деталями-задания)

---

## Цветовая палитра

### Основные цвета
- **Основной синий:** `#3498db` - Используется для основных кнопок, ссылок и выделений
- **Тёмно-синий:** `#2c3e50` - Используется для заголовков и тёмного фона
- **Зелёный (успех):** `#27ae60` - Используется для состояний успеха и выполненных задач
- **Красный (ошибка):** `#e74c3c` - Используется для сообщений об ошибках и действий удаления

### Нейтральные цвета
- **Белый:** `#ffffff` - Основной цвет фона
- **Светло-серый 1:** `#f5f7fa` - Вторичный цвет фона
- **Светло-серый 2:** `#f8f9fa` - Фон карточек и панелей
- **Светло-серый 3:** `#ecf0f1` - Границы и разделители
- **Средне-серый:** `#7f8c8d` - Вторичный текст и иконки
- **Тёмно-серый:** `#333333` - Основной цвет текста

<img width="1117" alt="image" src="https://github.com/user-attachments/assets/ee2046c8-1471-484a-973b-ceb68a1bc9f5" />

---

## Типографика

### Семейства шрифтов
- **Основной шрифт:** 'Segoe UI', Tahoma, Geneva, Verdana, sans-serif
- **Шрифт для кода:** 'Consolas', 'Monaco', 'Courier New', monospace (для SQL-редактора)

### Размеры шрифтов
- **Очень большой:** 2.5rem (40px) - Основной заголовок страницы
- **Большой:** 1.5rem (24px) - Заголовки разделов, заголовок дашборда
- **Средний:** 1.1rem (17.6px) - Заголовки карточек, важная информация
- **Базовый:** 1rem (16px) - Обычный текст, кнопки
- **Маленький:** 0.9rem (14.4px) - Вторичная информация, метки
- **Очень маленький:** 0.8rem (12.8px) - Подсказки, вспомогательная информация

### Толщина шрифта
- **Обычный:** 400
- **Средний:** 500
- **Жирный:** 600-700

<img width="1111" alt="image" src="https://github.com/user-attachments/assets/eba33aff-8876-440c-887c-c5526cb38210" />

---

## Общие компоненты

### Кнопки

#### Основная кнопка
- **Цвета:** Фон: `#3498db`, Текст: белый
- **Размер:** Padding: 0.75rem 1.5rem, Font-size: 1rem
- **Граница:** Отсутствует, Border-radius: 4px
- **Состояние при наведении:** Фон: `#2980b9`
- **Примеры использования:** "Войти", "Отправить решение", "Выполнить запрос"
- **CSS-класс:** `.btn.primary-btn`

#### Кнопка успеха
- **Цвета:** Фон: `#27ae60`, Текст: белый
- **Размер:** Padding: 0.75rem 1.5rem, Font-size: 1rem
- **Граница:** Отсутствует, Border-radius: 4px
- **Состояние при наведении:** Фон: `#219955`
- **Примеры использования:** "Отправить решение"
- **CSS-класс:** `.btn.success-btn`

#### Вторичная/Контурная кнопка
- **Цвета:** Фон: `#f1f1f1`, Текст: `#555`
- **Размер:** Padding: 0.6rem 1rem, Font-size: 0.9rem
- **Граница:** 1px solid `#ddd`, Border-radius: 4px
- **Состояние при наведении:** Фон: `#e5e5e5`
- **Примеры использования:** "Очистить фильтры"
- **CSS-класс:** `.clear-filters-btn`

#### Кнопка опасности
- **Цвета:** Фон: `rgba(231, 76, 60, 0.8)`, Текст: белый
- **Размер:** Padding: 0.5rem 1rem, Font-size: 0.9rem
- **Граница:** Отсутствует, Border-radius: 4px
- **Состояние при наведении:** Фон: `rgba(231, 76, 60, 1)`
- **Примеры использования:** "Выйти"
- **CSS-класс:** `#logout-btn`

<img width="1108" alt="image" src="https://github.com/user-attachments/assets/34ba9cbe-f787-47f7-abe7-bd4973e49f56" />


### Элементы форм

#### Текстовый ввод
- **Цвета:** Граница: `#ddd`, Текст: `#333`, Фон: белый
- **Размер:** Padding: 0.75rem, Font-size: 1rem, Width: 100%
- **Граница:** 1px solid `#ddd`, Border-radius: 4px
- **Состояние при фокусе:** Border-color: `#3498db`, Box-shadow: 0 0 0 2px rgba(52, 152, 219, 0.2)
- **Примеры использования:** Поля для имени пользователя/пароля
- **CSS-селектор:** `input[type="text"], input[type="password"], input[type="email"]`

#### Выпадающий список
- **Цвета:** Граница: `#ddd`, Текст: `#333`, Фон: белый
- **Размер:** Padding: 0.6rem 2rem 0.6rem 1rem, Font-size: 0.9rem
- **Граница:** 1px solid `#ddd`, Border-radius: 4px
- **Собственная стрелка:** 6px треугольник цвета `#555`
- **Примеры использования:** Фильтр сложности, фильтр статуса
- **CSS-класс:** `.custom-select select`

<img width="1110" alt="image" src="https://github.com/user-attachments/assets/1b95fc38-33a5-441f-bb85-dfd48f51d57b" />


### Карточки и контейнеры

#### Стандартная карточка
- **Цвета:** Фон: белый, Граница: `#ecf0f1` (иногда неявно через тень)
- **Размер:** Padding: 1.5-2rem, Border-radius: 8px
- **Тень:** 0 2px 4px rgba(0, 0, 0, 0.1)
- **Примеры использования:** Карточка статистики, карточки заданий
- **CSS-класс:** `.stats-card, .task-card`

#### Контейнер раздела
- **Цвета:** Фон: белый, Border-bottom: 1px solid `#ecf0f1`
- **Размер:** Margin-bottom: 2rem, Padding-bottom: 1rem
- **Примеры использования:** Разделы схемы, схема результатов
- **CSS-класс:** `.schema-section`

<img width="1116" alt="image" src="https://github.com/user-attachments/assets/0c6c7c2b-2f3f-4122-8131-9dab40276ee2" />


---

## Страница входа/регистрации

### Контейнер страницы
- **Max-width:** 1200px
- **Padding:** 2rem
- **CSS-класс:** `.container`

### Заголовок
- **Заголовок:** Font-size: 2.5rem, Цвет: `#2c3e50`, Margin-bottom: 0.5rem
- **Подзаголовок:** Font-size: 1.1rem, Цвет: `#7f8c8d`
- **CSS-класс:** `header h1, header p`

### Контейнер авторизации
- **Max-width:** 500px
- **Фон:** белый
- **Border-radius:** 8px
- **Тень:** 0 4px 6px rgba(0, 0, 0, 0.1)
- **CSS-класс:** `.auth-container`

### Вкладки авторизации
- **Цвета:** Активная вкладка: `#f8f9fa` с нижней границей `#3498db`, Неактивная: прозрачная
- **Размер:** Padding: 1rem
- **Шрифт:** Размер: 1rem, Вес: обычный (жирный для активной)
- **CSS-класс:** `.tab-btn, .tab-btn.active`

### Группы формы
- **Margin-bottom:** 1.5rem
- **Метка:** Display: block, Margin-bottom: 0.5rem, Font-weight: 500
- **CSS-класс:** `.form-group`

### Сообщения об ошибках
- **Цвет:** `#e74c3c`
- **Шрифт:** Размер: 0.9rem
- **Margin-top:** 1rem
- **CSS-класс:** `.error-message`

<img width="717" alt="image" src="https://github.com/user-attachments/assets/a1d6c48c-b96c-4024-928f-34072c21cbf4" />


---

## Страница дашборда

### Заголовок дашборда
- **Цвета:** Фон: `#2c3e50`, Текст: белый
- **Размер:** Padding: 1rem 2rem
- **Тень:** 0 2px 4px rgba(0, 0, 0, 0.1)
- **CSS-класс:** `.dashboard-header`

### Логотип
- **Шрифт:** Размер: 1.5rem, Вес: 600, Цвет: белый
- **Letter-spacing:** 0.5px
- **CSS-класс:** `.logo h1`

### Информация о пользователе
- **Имя пользователя:** Font-weight: 500
- **Промежуток между элементами:** 1rem
- **CSS-класс:** `.user-info, #username`

### Содержимое дашборда
- **Макет:** Flex с gap: 2rem, Padding: 2rem
- **CSS-класс:** `.dashboard-content`

### Боковая панель статистики
- **Ширина:** 300px
- **CSS-класс:** `.stats-sidebar`

### Карточка статистики
- **Цвета:** Фон: белый
- **Padding:** 1.5rem
- **Border-radius:** 8px
- **Тень:** 0 2px 4px rgba(0, 0, 0, 0.1)
- **Заголовок:** Margin-bottom: 1rem, Цвет: `#2c3e50`
- **CSS-класс:** `.stats-card, .stats-card h3`

### Индикатор прогресса
- **Высота:** 10px
- **Цвета:** Фон: `#ecf0f1`, Прогресс: `#3498db`
- **Border-radius:** 5px
- **Margin-bottom:** 0.5rem
- **CSS-класс:** `.progress-bar, .progress`

### Текст прогресса
- **Выравнивание:** По правому краю
- **Шрифт:** Размер: 0.9rem, Цвет: `#7f8c8d`
- **CSS-класс:** `.progress-text`

### Детали статистики
- **Макет:** Flex с space-between
- **Шрифт:** Метка, размер: 0.9rem, Цвет: `#7f8c8d`
- **Шрифт:** Значение, размер: 1.5rem, Вес: жирный, Цвет: `#2c3e50`
- **CSS-класс:** `.stats-details, .stat-label, .stat-value`

### Контейнер заданий
- **Заголовок:** Margin-bottom: 1.5rem, Цвет: `#2c3e50`
- **CSS-класс:** `.tasks-container h2`

### Элементы управления фильтром
- **Макет:** Flex с gap: 1rem, Margin-bottom: 1.5rem
- **Шрифт:** Заголовок, вес: 500, Цвет: `#555`
- **CSS-класс:** `.filter-controls, .filter-section-title`

### Сетка заданий
- **Макет:** Сетка с 3 колонками (адаптивная)
- **Промежуток:** 1.5rem
- **Margin-top:** 1.5rem
- **CSS-класс:** `.tasks-grid`

### Карточка задания
- **Цвета:** Фон: белый
- **Размер:** Высота: 160px
- **Border-radius:** 8px
- **Тень:** 0 2px 4px rgba(0, 0, 0, 0.1)
- **При наведении:** Transform: translateY(-3px), Shadow: 0 4px 8px rgba(0, 0, 0, 0.15)
- **CSS-класс:** `.task-card`

### Заголовок карточки задания
- **Padding:** 1rem
- **ID задания:** Font-size: 0.85rem, Цвет: `#7f8c8d`
- **Название задания:** Font-size: 1.1rem, Weight: 500, Цвет: `#2c3e50`
- **CSS-класс:** `.task-card-header, .task-id, .task-card-title`

### Нижняя часть карточки задания
- **Цвета:** Фон: `#f8f9fa`, Border-top: 1px solid `#ecf0f1`
- **Padding:** 0.75rem 1rem
- **Макет:** Flex с space-between
- **Шрифт:** Размер: 0.85rem
- **CSS-класс:** `.task-card-footer`

### Метки сложности
- **Легкое:** Фон: `#e8f5e9`, Цвет: `#2e7d32`
- **Среднее:** Фон: `#fff8e1`, Цвет: `#f57f17`
- **Сложное:** Фон: `#ffebee`, Цвет: `#c62828`
- **Padding:** 0.25rem 0.5rem
- **Border-radius:** 4px
- **Шрифт:** Размер: 0.8rem, Вес: жирный
- **CSS-класс:** `.task-difficulty.easy, .task-difficulty.medium, .task-difficulty.hard`

### Статус задания
- **Решено:** Цвет: `#27ae60`
- **Не решено:** Цвет: `#7f8c8d`
- **Шрифт:** Размер: 0.85rem
- **CSS-класс:** `.task-card-status.solved, .task-card-status.unsolved`

<img width="1484" alt="image" src="https://github.com/user-attachments/assets/fb694657-6de6-4747-aa57-c6bcf18bd997" />

---

## Страница с деталями задания

### Заголовок задания
- **Заголовок:** Размер шрифта варьируется, Цвет: унаследованный
- **Margin-bottom:** 2rem
- **CSS-класс:** `.task-header`

### Панель информации о задании
- **Макет:** Flex с gap: 1rem
- **Margin-top:** 0.5rem
- **CSS-класс:** `.task-info-bar`

### Содержимое задания
- **Цвета:** Фон: белый
- **Padding:** 2rem
- **Border-radius:** 8px
- **Тень:** 0 2px 4px rgba(0, 0, 0, 0.1)
- **CSS-класс:** `.task-content`

### Описание задания
- **Margin-bottom:** 2rem
- **Line-height:** 1.6
- **CSS-класс:** `.task-description`

### Раздел схемы
- **Margin-bottom:** 2rem
- **Padding-bottom:** 1rem
- **Border-bottom:** 1px solid `#ecf0f1`
- **Заголовок:** Margin-bottom: 1rem, Цвет: `#2c3e50`
- **CSS-класс:** `.schema-section, .schema-section h3`

### Таблица схемы
- **Margin-bottom:** 1.5rem
- **CSS-класс:** `.schema-table`

### Заголовок таблицы схемы
- **Макет:** Flex с align-items: center
- **Margin-bottom:** 0.5rem
- **CSS-класс:** `.schema-table-header`

### Имя таблицы схемы
- **Шрифт:** Вес: жирный, Цвет: `#3498db`
- **Margin-right:** 8px
- **CSS-класс:** `.schema-table-name`

### Кнопка копирования
- **Цвета:** Обычное состояние: `#7f8c8d`, При наведении: `#3498db`, Фон при наведении: `#f5f5f5`
- **Размер:** Padding: 4px
- **Border-radius:** 4px
- **Шрифт:** Размер: 0.8rem, Размер иконки: 14px
- **Переход:** scale(0.85) при активном состоянии
- **CSS-класс:** `.copy-btn`

### Обертка таблицы схемы
- **Граница:** 1px solid `#ecf0f1`
- **Border-radius:** 4px
- **CSS-класс:** `.schema-table-wrapper`

### Содержимое таблицы схемы
- **Min-width:** 500px (для прокрутки)
- **Заголовки:** Фон: `#ecf0f1`, Padding: 0.75rem, Text-align: left, Font-weight: bold
- **Ячейки:** Padding: 0.75rem, Border-bottom: 1px solid `#ddd`
- **Четные строки:** Фон: `#f9f9f9`
- **CSS-класс:** `table.schema-table-content`

<img width="954" alt="image" src="https://github.com/user-attachments/assets/798f585a-687f-4279-9459-392797e041f7" />

### SQL-редактор
- **Шрифт:** Семейство: 'Consolas', 'Monaco', 'Courier New', monospace, Размер: 14px
- **Высота:** auto, Min-height: 150px
- **Граница:** 1px solid `#ddd`, Border-radius: 4px
- **Line height:** 1.6
- **CSS-класс:** `.CodeMirror`

### Контейнер редактора
- **Margin-bottom:** 1.5rem
- **CSS-класс:** `.editor-container`

### Панель кнопок
- **Макет:** Flex с gap: 1rem
- **Margin-bottom:** 1rem
- **CSS-класс:** `.button-bar`

### Раздел результатов
- **Заголовок:** Margin-bottom: 1rem, Цвет: `#2c3e50`
- **CSS-класс:** `.result-section h3`

### Контейнер результатов
- **Граница:** 1px solid `#ddd`
- **Border-radius:** 4px
- **Нет результатов:** Padding: 2rem, Text-align: center, Цвет: `#7f8c8d`
- **CSS-класс:** `.results-container, .no-results`

### Таблица результатов
- **Ширина:** 100%
- **Заголовки:** Фон: `#ecf0f1`, Padding: 0.75rem, Text-align: left, Font-weight: bold
- **Ячейки:** Padding: 0.75rem, Border-bottom: 1px solid `#ddd`
- **Четные строки:** Фон: `#f9f9f9`
- **CSS-класс:** `.results-table`

### Сообщение об успехе
- **Цвета:** Фон: `#e8f5e9`, Граница: 1px solid `#c8e6c9`
- **Padding:** 1.5rem
- **Margin-top:** 2rem
- **Text-align:** center
- **Border-radius:** 4px
- **Заголовок:** Цвет: `#2e7d32`, Margin-bottom: 0.5rem
- **CSS-класс:** `.success-message, .success-message h3`

<img width="979" alt="image" src="https://github.com/user-attachments/assets/10d82238-5cf3-40bb-b575-41b6363ad217" />
