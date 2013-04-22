import os
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
from giotto.utils import better_base
from giotto.keyvalue import DatabaseKeyValue

Base = better_base()

from sqlite3 import dbapi2 as sqlite
engine = create_engine('sqlite+pysqlite:///file.db', module=sqlite)

session = sessionmaker(bind=engine)()
cache = DatabaseKeyValue(Base, session)
auth_session = cache
auth_session_expire = 3600 * 24 * 7

project_path = os.path.dirname(os.path.abspath(__file__))

from jinja2 import Environment, FileSystemLoader
jinja2_env = Environment(loader=FileSystemLoader(os.path.join(project_path, 'html')))

debug = True
error_template = None

server_url = "http://localhost:5000"