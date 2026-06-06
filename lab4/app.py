from flask import Flask, render_template, request, session, redirect, url_for, flash, g
from flask_login import LoginManager, UserMixin, login_user, login_required, logout_user, current_user
from werkzeug.security import generate_password_hash, check_password_hash
from config import Config
from db import get_db, close_db, init_db
import random
from faker import Faker
from datetime import datetime
import re

fake = Faker('ru_RU')

app = Flask(__name__)
app.config.from_object(Config)
application = app

# Flask-Login настройка
login_manager = LoginManager()
login_manager.init_app(app)
login_manager.login_view = 'login'
login_manager.login_message = 'Для доступа к этой странице необходимо войти в систему.'
login_manager.login_message_category = 'warning'

# закрытие соединения с БД после запроса
app.teardown_appcontext(close_db)


class User(UserMixin):
    def __init__(self, id, login, password_hash, first_name, last_name=None, middle_name=None, role_id=None):
        self.id = id
        self.login = login
        self.password_hash = password_hash
        self.first_name = first_name
        self.last_name = last_name
        self.middle_name = middle_name
        self.role_id = role_id

    @property
    def full_name(self):
        parts = [self.last_name, self.first_name, self.middle_name]
        return ' '.join(p for p in parts if p)

    @property
    def role_name(self):
        db = get_db()
        row = db.execute('SELECT name FROM roles WHERE id = ?', (self.role_id,)).fetchone()
        return row['name'] if row else None

@login_manager.user_loader
def load_user(user_id):
    db = get_db()
    row = db.execute('SELECT * FROM users WHERE id = ?', (user_id,)).fetchone()
    if row is None:
        return None
    return User(row['id'], row['login'], row['password_hash'],
                row['first_name'], row['last_name'],
                row['middle_name'], row['role_id'])


def generate_comments(replies=True, level=0):
    comments = []
    for i in range(random.randint(1, 3)):
        comment = {
            'author': fake.name(),
            'text': fake.paragraph(nb_sentences=2),
            'date': fake.date_time_between(start_date='-30d', end_date='now')
        }
        if replies and level < 2:
            comment['replies'] = generate_comments(replies=False, level=level+1)
        comments.append(comment)
    return comments

image_ids = ['1.jpg', '2.jpg', '3.jpg', '4.jpg', '5.jpg']

def generate_post(index):
    return {
        'id': index,
        'title': fake.sentence(nb_words=5),
        'text': fake.paragraph(nb_sentences=20),
        'author': fake.name(),
        'date': fake.date_time_between(start_date='-2y', end_date='now'),
        'image_id': random.choice(image_ids),
        'comments': generate_comments()
    }

posts = [generate_post(i) for i in range(5)]
posts.sort(key=lambda x: x['date'], reverse=True)


def validate_login(login):
    errors = []
    if not login:
        errors.append('Поле не может быть пустым.')
    elif not re.fullmatch(r'[a-zA-Z0-9]{5,}', login):
        errors.append('Логин должен содержать только латинские буквы и цифры, минимум 5 символов.')
    return errors

def validate_password(password):
    errors = []
    allowed_special = r'~!?@#$%^&*_\-+()\[\]{}<>/\\|"\'.,:;'
    if not password:
        errors.append('Поле не может быть пустым.')
        return errors
    if len(password) < 8:
        errors.append('Пароль должен содержать не менее 8 символов.')
    if len(password) > 128:
        errors.append('Пароль должен содержать не более 128 символов.')
    if not re.search(r'[A-ZА-ЯЁ]', password):
        errors.append('Пароль должен содержать хотя бы одну заглавную букву.')
    if not re.search(r'[a-zа-яё]', password):
        errors.append('Пароль должен содержать хотя бы одну строчную букву.')
    if not re.search(r'[0-9]', password):
        errors.append('Пароль должен содержать хотя бы одну цифру.')
    if re.search(r'\s', password):
        errors.append('Пароль не должен содержать пробелы.')
    if not re.fullmatch(rf'[a-zA-Zа-яА-ЯёЁ0-9{re.escape(allowed_special)}]+', password):
        errors.append('Пароль содержит недопустимые символы.')
    return errors

def validate_user_form(form, is_create=True):
    field_errors = {}
    if is_create:
        login_errors = validate_login(form.get('login', '').strip())
        if login_errors:
            field_errors['login'] = login_errors
        password_errors = validate_password(form.get('password', ''))
        if password_errors:
            field_errors['password'] = password_errors
    if not form.get('first_name', '').strip():
        field_errors['first_name'] = ['Поле не может быть пустым.']
    return field_errors


@app.route('/')
def index():
    return render_template('index.html', title='Главная')

@app.route('/posts')
def posts_list():
    return render_template('posts.html', title='Посты', posts=posts)

@app.route('/posts/<int:post_id>')
def post_detail(post_id):
    post = posts[post_id]
    return render_template('post.html', title=post['title'], post=post)


@app.route('/request-url')
def request_url():
    return render_template('request_url.html', title='Параметры URL', url_params=request.args)

@app.route('/request-headers')
def request_headers():
    return render_template('request_headers.html', title='Заголовки запроса', headers=request.headers)

@app.route('/request-cookies')
def request_cookies():
    return render_template('request_cookies.html', title='Cookie', cookies=request.cookies)

def validate_phone(phone):
    if re.search(r'[^\d\s\(\)\-\.\+]', phone):
        return None, 'Недопустимый ввод. В номере телефона встречаются недопустимые символы.'
    
    digits = re.sub(r'\D', '', phone)
    phone_stripped = phone.strip()
    
    if phone_stripped.startswith('+7') or phone_stripped.startswith('8'):
        expected_len = 11
    else:
        expected_len = 10
    
    if len(digits) != expected_len:
        return None, 'Недопустимый ввод! Неверное количество цифр.'
    
    if len(digits) == 10:
        digits = '8' + digits
    
    formatted = f'8-{digits[1:4]}-{digits[4:7]}-{digits[7:9]}-{digits[9:11]}'
    return formatted, None

@app.route('/phone', methods=['GET', 'POST'])
def phone():
    phone_input = ''
    formatted = None
    error = None
    
    if request.method == 'POST':
        phone_input = request.form.get('phone', '')
        formatted, error = validate_phone(phone_input)
    
    return render_template('phone.html', title='Проверка телефона',
                          phone_input=phone_input, formatted=formatted, error=error)


@app.route('/counter')
def counter():
    visits = session.get('counter_visits', 0)
    session['counter_visits'] = visits + 1
    return render_template('counter.html', title='Счётчик посещений', visits=visits + 1)

@app.route('/login', methods=['GET', 'POST'])
def login():
    if current_user.is_authenticated:
        return redirect(url_for('users_index'))
    
    if request.method == 'POST':
        username = request.form.get('username')
        password = request.form.get('password')
        remember = 'remember' in request.form
        
        db = get_db()
        user_row = db.execute('SELECT * FROM users WHERE login = ?', (username,)).fetchone()
        
        if user_row and check_password_hash(user_row['password_hash'], password):
            user = User(user_row['id'], user_row['login'], user_row['password_hash'],
                       user_row['first_name'], user_row['last_name'],
                       user_row['middle_name'], user_row['role_id'])
            login_user(user, remember=remember)
            flash('Успешный вход в систему!', 'success')
            
            next_page = request.args.get('next')
            return redirect(next_page) if next_page else redirect(url_for('users_index'))
        else:
            flash('Неверный логин или пароль!', 'danger')
    
    return render_template('login.html', title='Вход')

@app.route('/secret')
@login_required
def secret():
    return render_template('secret.html', title='Секретная страница')

@app.route('/logout')
@login_required
def logout():
    logout_user()
    flash('Вы вышли из системы.', 'info')
    return redirect(url_for('index'))



# список пользователей
@app.route('/users')
def users_index():
    db = get_db()
    users = db.execute('''
        SELECT u.*, r.name as role_name
        FROM users u
        LEFT JOIN roles r ON u.role_id = r.id
        ORDER BY u.id
    ''').fetchall()
    return render_template('users/index.html', title='Пользователи', users=users)

# просмотр пользователя
@app.route('/users/<int:user_id>')
@login_required
def user_view(user_id):
    db = get_db()
    user = db.execute('''
        SELECT u.*, r.name as role_name
        FROM users u
        LEFT JOIN roles r ON u.role_id = r.id
        WHERE u.id = ?
    ''', (user_id,)).fetchone()
    if user is None:
        flash('Пользователь не найден.', 'danger')
        return redirect(url_for('users_index'))
    return render_template('users/view.html', title='Просмотр пользователя', user=user)

# создание пользователя
@app.route('/users/create', methods=['GET', 'POST'])
@login_required
def user_create():
    db = get_db()
    roles = db.execute('SELECT * FROM roles').fetchall()
    form_data = {}
    field_errors = {}
    
    if request.method == 'POST':
        form_data = request.form
        field_errors = validate_user_form(form_data, is_create=True)
        
        if not field_errors:
            try:
                db.execute('''
                    INSERT INTO users (login, password_hash, last_name, first_name, middle_name, role_id)
                    VALUES (?, ?, ?, ?, ?, ?)
                ''', (
                    form_data['login'].strip(),
                    generate_password_hash(form_data['password']),
                    form_data.get('last_name', '').strip() or None,
                    form_data['first_name'].strip(),
                    form_data.get('middle_name', '').strip() or None,
                    form_data.get('role_id') or None
                ))
                db.commit()
                flash('Пользователь успешно создан!', 'success')
                return redirect(url_for('users_index'))
            except Exception as e:
                db.rollback()
                flash(f'Ошибка при создании: {e}', 'danger')
    
    return render_template('users/create.html', title='Создание пользователя',
                          roles=roles, form_data=form_data, field_errors=field_errors)

# редактирование пользователя
@app.route('/users/<int:user_id>/edit', methods=['GET', 'POST'])
@login_required
def user_edit(user_id):
    db = get_db()
    user = db.execute('SELECT * FROM users WHERE id = ?', (user_id,)).fetchone()
    if user is None:
        flash('Пользователь не найден.', 'danger')
        return redirect(url_for('users_index'))
    
    roles = db.execute('SELECT * FROM roles').fetchall()
    field_errors = {}
    form_data = dict(user)
    
    if request.method == 'POST':
        form_data = request.form
        field_errors = validate_user_form(form_data, is_create=False)
        
        if not field_errors:
            try:
                db.execute('''
                    UPDATE users
                    SET last_name=?, first_name=?, middle_name=?, role_id=?
                    WHERE id=?
                ''', (
                    form_data.get('last_name', '').strip() or None,
                    form_data['first_name'].strip(),
                    form_data.get('middle_name', '').strip() or None,
                    form_data.get('role_id') or None,
                    user_id
                ))
                db.commit()
                flash('Пользователь успешно обновлён!', 'success')
                return redirect(url_for('users_index'))
            except Exception as e:
                db.rollback()
                flash(f'Ошибка при обновлении: {e}', 'danger')
    
    return render_template('users/edit.html', title='Редактирование пользователя',
                          user=user, roles=roles, form_data=form_data, field_errors=field_errors)

# удаление пользователя
@app.route('/users/<int:user_id>/delete', methods=['POST'])
@login_required
def user_delete(user_id):
    # 1. Запрет на самоудаление
    if user_id == current_user.id:
        flash('Вы не можете удалить самого себя!', 'danger')
        return redirect(url_for('users_index'))
    
    db = get_db()
    
    # 2. Проверка: если удаляем администратора
    user_to_delete = db.execute('SELECT role_id FROM users WHERE id = ?', (user_id,)).fetchone()
    
    if user_to_delete and user_to_delete['role_id'] == 1:
        # Считаем, сколько всего администраторов в БД
        admin_count = db.execute('SELECT COUNT(*) as count FROM users WHERE role_id = 1').fetchone()['count']
        
        if admin_count <= 1:
            flash('Нельзя удалить последнего администратора!', 'danger')
            return redirect(url_for('users_index'))

    try:
        db.execute('DELETE FROM users WHERE id = ?', (user_id,))
        db.commit()
        flash('Пользователь успешно удалён.', 'success')
    except Exception as e:
        db.rollback()
        flash(f'Ошибка при удалении: {e}', 'danger')
    return redirect(url_for('users_index'))

# смена пароля
@app.route('/change-password', methods=['GET', 'POST'])
@login_required
def change_password():
    field_errors = {}
    if request.method == 'POST':
        old_password = request.form.get('old_password', '')
        new_password = request.form.get('new_password', '')
        confirm_password = request.form.get('confirm_password', '')
        
        if not check_password_hash(current_user.password_hash, old_password):
            field_errors['old_password'] = ['Неверный текущий пароль.']
        password_errors = validate_password(new_password)
        if password_errors:
            field_errors['new_password'] = password_errors
        if new_password != confirm_password:
            field_errors['confirm_password'] = ['Пароли не совпадают.']
        
        if not field_errors:
            try:
                db = get_db()
                db.execute('UPDATE users SET password_hash = ? WHERE id = ?',
                          (generate_password_hash(new_password), current_user.id))
                db.commit()
                flash('Пароль успешно изменён!', 'success')
                return redirect(url_for('users_index'))
            except Exception as e:
                flash(f'Ошибка: {e}', 'danger')
    
    return render_template('change_password.html', title='Изменение пароля', field_errors=field_errors)

if __name__ == '__main__':
    init_db(app)
    app.run(debug=True)