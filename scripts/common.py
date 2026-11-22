from pathlib import Path
import os
from dotenv import load_dotenv
from sqlalchemy import create_engine, URL

ROOT = Path(__file__).resolve().parents[1]
load_dotenv(ROOT / '.env')

def engine(with_database=True):
    name = os.getenv('DB_NAME', 'volleyball_db')
    if name != 'volleyball_db':
        raise ValueError('This project uses DB_NAME=volleyball_db')
    return create_engine(URL.create('mysql+pymysql',
        username=os.getenv('DB_USER', 'volleyball_user'),
        password=os.environ['DB_PASSWORD'],
        host=os.getenv('DB_HOST', '127.0.0.1'),
        port=int(os.getenv('DB_PORT', '3307')),
        database=name if with_database else None,
        query={'charset': 'utf8mb4'}), pool_pre_ping=True)

def statements(path):
    # SQL in this project contains no semicolons inside string literals.
    return [s.strip() for s in path.read_text(encoding='utf-8-sig').split(';') if s.strip()]
