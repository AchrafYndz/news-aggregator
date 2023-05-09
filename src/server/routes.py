import json

from flask.templating import render_template
from flask import request, session, jsonify, redirect, flash, json, make_response, request
from forms import RegisterForm, LoginForm
from flask_login import login_user, logout_user, current_user
from wtforms import Form, StringField, TextAreaField, validators
from flask_wtf import csrf
from werkzeug.datastructures import MultiDict


from src.server.app import app
from src.server.config import app_data, db
from src.server.ArticlesFetcher import fetch
from src.server.ConnectDB import ConnectDB
from src.server.database import User, RSS, TF_IDF
from search import search
from sqlalchemy import asc, or_

# REST API
# See https://www.ibm.com/developerworks/library/ws-restful/index.html

ConnectDB = ConnectDB(db)


@app.route("/api/rss", methods=['POST'])
def post_rss():
    feed_data = request.get_json()

    success, message = ConnectDB.addRSS(feed_data['feed_name'], feed_data['feed_url'])

    return message, success


# @app.route("/api/post_admin", methods=['POST'])
# def post_admin():
#     admin_data = request.get_json()
#     success, message = ConnectDB.addAdmin(admin_data['admin_name'], admin_data['admin_password'])
#
#     return message, success


@app.route("/api/admins", methods=['DELETE'])
def delete_admin():
    name = request.args.get('name', type=str)
    success = User.query.filter_by(username=name).delete()
    db.session.commit()
    return {'message': 'Admin deleted successfully', "status": 200} if success \
        else {'message': 'Could not delete admin', "status": 500}

@app.route("/api/rss", methods=['DELETE'])
def delete_feed():
    delete_id = request.args.get('delete_id', type=int)
    success = RSS.query.filter(RSS.id == delete_id).delete()
    db.session.commit()
    return {'message': 'RSS Feed deleted successfully', "status": 200} if success \
        else {'message': 'Could not delete RSS Feed', "status": 500}


@app.route("/api/articles", methods=['GET'])
def get_articles():
    skip = request.args.get('offset', type=int)


    articles = fetch(skip)
    return json.dumps(articles)

@app.route("/api/similarity/", methods=['GET'])
def get_similar_articles():
    article_link = request.args.get('article_link', type=str)
    # Retrieve all rows in the tf_idf table where the given article ID is present
    rows = db.session.query(TF_IDF).filter(or_(TF_IDF.article1 == article_link, TF_IDF.article2 == article_link)).all()

    # Create a set of unique article IDs that are similar to the given article ID
    similar_articles = set()
    for row in rows:
        if row.article1 == article_link:
            similar_articles.add(row.article2)
        else:
            similar_articles.add(row.article1)

    # Convert the set of similar article IDs to a list and return it as a JSON response
    return jsonify(list(similar_articles))

@app.route("/api/search", methods=['GET'])
def get_search():
    query_string = request.args.get('q', type=str)
    articles = search(query_string)
    return json.dumps(articles)


@app.route("/api/rss", methods=['GET'])
def get_feeds():
    db_feeds = RSS.query.order_by(asc(RSS.id)).all()

    feeds = []

    for db_feed in db_feeds:
        feed = {
            "id": db_feed.id,
            "url": db_feed.rss_url,
            "name": db_feed.name
        }
        feeds.append(feed)

    return json.dumps(feeds)


@app.route("/api/admins", methods=['GET'])
def get_admins():
    db_admins = User.query.filter_by(is_admin=True).order_by(asc(User.username)).all()

    admins = []

    for db_admin in db_admins:
        admin = {
            "name": db_admin.username,
        }
        admins.append(admin)

    return json.dumps(admins)


@app.errorhandler(404)
def not_found_error(error):
    return jsonify({'error': 'Page not found'}), 404


@app.errorhandler(403)
def forbidden_error(error):
    return jsonify({'error': 'Forbidden'}), 403


@app.errorhandler(500)
def internal_server_error(error):
    return jsonify({'error': 'Internal server error'}), 500


@app.route('/api/csrf_token', methods=['GET'])
def get_csrf_token():
    csrf_token = csrf.generate_csrf()
    return jsonify({'csrf_token': csrf_token})


@app.route("/api/@me", methods=['GET'])
def get_current_user():
    if not current_user.is_authenticated:
        return jsonify({
            "error": "Unauthorized",
            "status": 401
        })
    return jsonify({
        "username": current_user.username,
        "is_admin": current_user.is_admin,
        "status": 200
    })


@app.route('/api/register', methods=['GET', 'POST'])
def register_page():
    form_data = MultiDict(request.get_json())
    form = RegisterForm(form_data)
    if form.validate():
        user_to_create = User(username=form.username.data,
                              email_address=form.email_address.data,
                              password=form.password1.data)
        db.session.add(user_to_create)
        db.session.commit()
        attempted_user = User.query.filter_by(username=form.username.data).first()
        login_user(attempted_user)
        if current_user.is_authenticated:
            return jsonify({'message': 'User created and logged in successfully'})
    if form.errors != {}:
        return jsonify({'errors': form.errors})


@app.route('/api/admins', methods=['POST'])
def register_page_admin():
    form_data = MultiDict(request.get_json())
    form = RegisterForm(form_data)
    if form.validate():
        user_to_create = User(username=form.username.data,
                              email_address=form.email_address.data,
                              password=form.password1.data,
                              is_admin=True)
        db.session.add(user_to_create)
        db.session.commit()
        attempted_user = User.query.filter_by(username=form.username.data).first()
        return jsonify({'message': 'Admin created successfully'})
    if form.errors != {}:
        return jsonify({'errors': form.errors})


@app.route('/api/login', methods=['GET', 'POST'])
def login_page():
    form_data = MultiDict(request.get_json())
    form = LoginForm(form_data)
    if form.validate_on_submit():
        attempted_user = User.query.filter_by(username=form.username.data).first()
        if attempted_user and attempted_user.check_password_correction(attempted_password=form.password.data):
            login_user(attempted_user)
            return jsonify({'message': 'User logged in successfully'})
        else:
            return jsonify({'errors': 'Username and password do not match! Please try again'})


@app.route('/api/logout')
def logout_page():
    logout_user()
    return {'message': 'Logged out successfully'}
