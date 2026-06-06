from flask import Flask, render_template, request
import random
from faker import Faker
from datetime import datetime
import re

fake = Faker('ru_RU')

app = Flask(__name__)
app.config['SECRET_KEY'] = 'secret-key-for-session'

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

@app.route('/login', methods=['GET', 'POST'])
def login():
    form_data = None
    if request.method == 'POST':
        form_data = {
            'username': request.form.get('username'),
            'password': request.form.get('password')
        }
    return render_template('login.html', title='Авторизация', form_data=form_data)

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
        return None, 'Недопустимый ввод. Неверное количество цифр.'
    
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

if __name__ == '__main__':
    app.run(debug=True)