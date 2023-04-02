##wrapper to use the database
from flask_sqlalchemy import SQLAlchemy
from database import User, RSS
from sqlalchemy import inspect


# from src.server.config import db


class ConnectDB():
    def __init__(self, db: SQLAlchemy):
        self.db = db
        self.counter = 1000

    def checkUserExisits(self, cookie):
        return self.db.session.query(User.cookie).filter_by(cookie=cookie).first() is not None

    def checkRSSExists(self, id):
        return self.db.session.query(RSS.id).filter_by(id=id).first() is not None

    def column_exists(self, table=None, column=None):
        found = False
        inspector = inspect(self.db.engine)
        schemas = inspector.get_schema_names()
        for schema in schemas:
            if schema == 'public':
                for table_name in inspector.get_table_names(schema=schema):
                    if str(table_name) == str(table):
                        for column_name in inspector.get_columns(table_name, schema=schema):
                            if str(column_name['name']) == str(column):
                                found = True
                                return found
        return found

    def table_exists(self, table):
        found = False
        inspector = inspect(self.db.engine)
        schemas = inspector.get_schema_names()
        for schema in schemas:
            if schema == 'public':
                for table_name in inspector.get_table_names(schema=schema):
                    if str(table_name) == str(table):
                        found = True
                        return found
        return found

    def column_in_schema(self, column):
        found = False
        inspector = inspect(self.db.engine)
        schemas = inspector.get_schema_names()
        for schema in schemas:
            if schema == 'public':
                for table_name in inspector.get_table_names(schema=schema):
                    for column_name in inspector.get_columns(table_name, schema=schema):
                        if str(column_name['name']) == str(column):
                            found = True
                            return found
        return found

    def addUser(self, cookie, history=""):
        u = User(cookie=cookie, history=history)
        if not self.checkUserExisits(cookie):
            self.db.session.add(u)
            self.db.session.commit()
        else:
            print("user already in db")
        # print(User.query.all())

    def addRSS(self, rss_url: str, published_by: str):
        rss = RSS(rss_url=rss_url, source_id=published_by)
        if not self.checkRSSExists(rss.id):
            self.db.session.add(rss)
            self.db.session.commit()
        else:
            print("rss already in db")
        # print(RSS.query.all())
