from flask import Flask, render_template
import random
from faker import Faker
from datetime import datetime

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

image_ids = [
    '1.jpg', '2.jpg', '3.jpg', '4.jpg', '5.jpg'
]

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

@app.route('/about')
def about():
    return render_template('about.html', title='Об авторе')

if __name__ == '__main__':
    app.run(debug=True)