-- таблица ролей
CREATE TABLE IF NOT EXISTS roles (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    name VARCHAR(100) NOT NULL,
    description TEXT
);

-- таблица пользователей
CREATE TABLE IF NOT EXISTS users (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    login VARCHAR(100) NOT NULL UNIQUE,
    password_hash VARCHAR(256) NOT NULL,
    last_name VARCHAR(100),
    first_name VARCHAR(100) NOT NULL,
    middle_name VARCHAR(100),
    role_id INTEGER,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    FOREIGN KEY (role_id) REFERENCES roles(id)
);

-- таблица журнала посещений
CREATE TABLE IF NOT EXISTS visit_logs (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    path VARCHAR(100) NOT NULL,
    user_id INTEGER,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    FOREIGN KEY (user_id) REFERENCES users(id)
);

-- начальные данные
INSERT OR IGNORE INTO roles (id, name, description) VALUES
    (1, 'Администратор', 'Полный доступ к системе'),
    (2, 'Пользователь', 'Обычный пользователь');

INSERT OR IGNORE INTO users (login, password_hash, last_name, first_name, middle_name, role_id)
VALUES ('admin', 'pbkdf2:sha256:600000$placeholder', 'Администраторов', 'Админ', NULL, 1);