import os

class Config:
    SECRET_KEY = 'your-secret-key-here'
    DB_PATH = os.path.join(os.path.dirname(__file__), 'database.db')