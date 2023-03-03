from datetime import datetime, date, time
import bcrypt
from flask_login import login_manager, UserMixin
from sqlalchemy import *
from sqlalchemy.orm import relationship, declarative_base, scoped_session, sessionmaker

from .con import engine

db_session = scoped_session(sessionmaker(autocommit=False,
                                         autoflush=False,
                                         bind=engine))

Base = declarative_base()
Base.query = db_session.query_property()


class User(Base, UserMixin):
    __tablename__ = 'user'
    cookie = Column(Integer, Sequence('user_seq'), primary_key=True)
    history = Column(String(255), nullable=True)
    id = Column(Integer(), primary_key=True)
    username = Column(String(30), nullable=False, unique=True)
    email_address = Column(String(50), nullable=False, unique=True)
    password_hash = Column(String(60), nullable=False)

    @property
    def password(self):
        # password_hash?
        return self.password

    @password.setter
    def password(self, plain_text_password):
        self.password_hash = bcrypt.generate_password_hash(plain_text_password).decode('utf-8')

    def check_password_correction(self, attempted_password):
        return bcrypt.check_password_hash(self.password_hash, attempted_password)


class Admin(Base):
    __tablename__ = 'admin'
    name = Column(String(255), primary_key=True)
    password_hash = Column(String, nullable=False)
    cookie_id = Column(Integer, ForeignKey('user.cookie', ondelete='CASCADE', onupdate='CASCADE'), unique=True)
    cookie = relationship('User', backref='user')


class Creates(Base):
    __tablename__ = 'creates'
    creator = Column(String, ForeignKey('admin.name', ondelete='CASCADE', onupdate='CASCADE'), primary_key=True)
    created = Column(String, ForeignKey('admin.name', ondelete='CASCADE', onupdate='CASCADE'), primary_key=True)


class NewsSource(Base):
    __tablename__ = 'source'
    name = Column(String, primary_key=True)
    magazine = Column(String, nullable=False)

class RSS(Base):
    __tablename__='rss'
    content = Column(TEXT,nullable=False)
    id = Column(INT,primary_key=True)
    published_by=Column(String,ForeignKey('source.name',ondelete='SET-NULL',onupdate='CASCADE'),nullable=False)

class Labels(Base):
    __tablename__='labels'
    label=Column(String,primary_key=True)

class Article(Base):
    __tablename__='article'
    title = Column(String,nullable=False)
    description = Column(String,nullable=True)
    photo = Column(String,nullable=True)
    link=Column(String,primary_key=True)
    pub_date=Column(String,nullable=False)
    pub_time = Column(String, nullable=False)
    references=Column(String,ForeignKey('source.name',onupdate='CASCADE',ondelete='CASCADE'),nullable=False)
    rss_access=Column(INT,ForeignKey('rss.id',onupdate='CASCADE',ondelete='CASCADE'),nullable=False)
    label=Column(String,ForeignKey('labels.label',onupdate='CASCADE',ondelete='CASCADE'),nullable=False)

class TF_IDF(Base):
    __tablename__='tf_idf'
    article1=Column(String,ForeignKey('article.link',ondelete='CASCADE',onupdate='CASCADE'),nullable=False,primary_key=True)
    article2=Column(String,ForeignKey('article.link',ondelete='CASCADE',onupdate='CASCADE'),nullable=False,primary_key=True)
    value=Column(INT,nullable=False)

class Feed(Base):
    __tablename__='feed'
    article=Column(String,ForeignKey('article.link',ondelete='CASCADE',onupdate='CASCADE'),nullable=False,primary_key=True)
    user=Column(INT,ForeignKey('user.cookie',ondelete='CASCADE',onupdate='CASCADE'),nullable=False,primary_key=True)

# connection.execute()
def create():
    Base.metadata.create_all(engine)


if __name__ == "__main__":
    create()
    # session.close_all()
