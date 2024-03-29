from datetime import datetime
import json

from flask import jsonify, json, request
from forms import RegisterForm, LoginForm
from flask_login import login_user, logout_user, current_user, login_required
from flask_wtf import csrf
from werkzeug.datastructures import MultiDict


from src.server.app import app
from src.server.config import app_data, db
from src.server.ArticlesFetcher import ArticlesFetcher
# from src.server.ArticlesFetcher import newFetch, newFetchPopular, get_article_by_label
from src.server.ConnectDB import ConnectDB
from src.server.database import User, RSS, TF_IDF, Article, History, Label, Article_Labels
from search import search
from sqlalchemy import asc, or_

from src.server.link_articles import from_same_site

# REST API
# See https://www.ibm.com/developerworks/library/ws-restful/index.html

ConnectDB = ConnectDB(db)
articles_fetcher = ArticlesFetcher()



# Add a feed to the database
@app.route("/api/rss", methods=['POST'])
@login_required
def post_rss():
    print("we get here", flush=True)
    feed_data = request.get_json()

    success, message = ConnectDB.addRSS(feed_data['feed_name'], feed_data['feed_url'])

    return message, success

# Delete an admin
@app.route("/api/admins", methods=['DELETE'])
@login_required
def delete_admin():
    name = request.args.get('name', type=str)
    success = User.query.filter_by(username=name).delete()
    db.session.commit()
    return {'message': 'Admin deleted successfully', "status": 200} if success \
        else {'message': 'Could not delete admin', "status": 500}

# Delete an rss feed
@app.route("/api/rss", methods=['DELETE'])
@login_required
def delete_feed():
    delete_id = request.args.get('delete_id', type=int)
    success = RSS.query.filter(RSS.id == delete_id).delete()
    db.session.commit()
    return {'message': 'RSS Feed deleted successfully', "status": 200} if success \
        else {'message': 'Could not delete RSS Feed', "status": 500}

# Return all articles
@app.route("/api/articles", methods=['GET'])
def get_articles():
    # GET http:/5001/articles?offset=0&sort="Recommended"&searchQuery=20&labels[]
    skip = request.args.get('offset', type=int)
    sort = request.args.get('sort', type=str)
    searchQuery = request.args.get('searchQuery', type=str)
    labels = request.args.getlist('labels[]')
    excluded = request.args.getlist('exclude[]')

    final_articles = []

    if searchQuery != "":
        final_articles = search(searchQuery)
    else:
        if sort == "Popularity":
            final_articles = articles_fetcher.fetch_popular(labels, excluded, skip)
        elif sort == "Recency":
            final_articles = articles_fetcher.fetch_recent(labels, excluded, skip)
        elif sort == "Recommended":
            final_articles = articles_fetcher.fetch_recommended(labels, current_user.id, excluded, skip)

    return json.dumps(final_articles)

# Return all labels
@app.route("/api/labels", methods=['GET'])
def get_labels():
    label_entries = Article_Labels.query.all()
    labels = list(set([label.label for label in label_entries]))

    return jsonify(labels)


# Return all similar articles
@app.route("/api/similarity/", methods=['GET'])
def get_similar_articles():
    article_link = request.args.get('article_link', type=str)
    # Retrieve all rows in the tf_idf table where the given article ID is present
    rows = db.session.query(TF_IDF).filter(or_(TF_IDF.article1 == article_link, TF_IDF.article2 == article_link)).all()

    # Create a set of unique article IDs that are similar to the given article ID
    similar_articles = set()
    for row in rows:
        if row.article1 == article_link and not from_same_site(row.article2, article_link):
            similar_articles.add(row.article2)
        elif not from_same_site(row.article1, article_link):
            similar_articles.add(row.article1)

    similar_articles = list(similar_articles)

    filtered_similar = set()
    for i, entry in enumerate(similar_articles):
        add = True
        for entry_2 in similar_articles[i+1:]:
            if from_same_site(entry, entry_2):
                add = False
        if add:
            filtered_similar.add(entry)

    # Convert the set of similar article IDs to a list and return it as a JSON response
    return jsonify(list(filtered_similar))

# Get all rss feeds
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
@login_required
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

# Get CSRF token
@app.route('/api/csrf_token', methods=['GET'])
def get_csrf_token():
    csrf_token = csrf.generate_csrf()
    return jsonify({'csrf_token': csrf_token})

# Return user identity
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


@app.route('/api/history', methods=['POST'])
@login_required
def click():
    user_id = current_user.id
    article_link = request.get_json().get('link')
    article = Article.query.filter_by(link=article_link).first()

    if article is None:
        return jsonify({'error': 'Article does not exist'})

    exists = History.query.filter_by(article_link=article_link).first()
    if exists:
        exists.read_on = datetime.now().strftime('%Y-%m-%d %H:%M:%S')
    else:
        history_to_add = History(
            user_id=user_id,
            article_link=article.link,
            read_on=datetime.now().strftime('%Y-%m-%d %H:%M:%S')
        )
        db.session.add(history_to_add)

    db.session.commit()
    return jsonify({'message': 'tracked history successfully'})

# Add a view to an article's counter
@app.route('/api/articles/view', methods=['PUT'])
def view():
    article = Article.query.filter_by(link=request.get_json().get('link')).first()
    if article is None:
        return jsonify({'error': 'Article does not exist'})
    article.views += 1
    db.session.commit()
    return jsonify({'message': 'view added successfully', "views": article.views})

# Add a user
@app.route('/api/users', methods=['POST'])
def register_user():
    form_data = MultiDict(request.get_json())
    form = RegisterForm(form_data)
    if form.validate():
        user_to_create = User(
            username=form.username.data,
            email_address=form.email_address.data,
            password=form.password1.data
        )
        db.session.add(user_to_create)
        db.session.commit()
        attempted_user = User.query.filter_by(username=form.username.data).first()
        login_user(attempted_user)
        if current_user.is_authenticated:
            return jsonify({'message': 'User created and logged in successfully'})
    if form.errors != {}:
        return jsonify({'errors': form.errors})

# Add an admin
@app.route('/api/admins', methods=['POST'])
@login_required
def register_admin():
    if not current_user.is_admin:
        return jsonify({'errors': 'You are not an admin'})
    form_data = MultiDict(request.get_json())
    form = RegisterForm(form_data)
    if form.validate():
        user_to_create = User(
            username=form.username.data,
            email_address=form.email_address.data,
            password=form.password1.data,
            is_admin=True
        )
        db.session.add(user_to_create)
        db.session.commit()
        return jsonify({'message': 'Admin created successfully'})
    if form.errors != {}:
        return jsonify({'errors': form.errors})

@app.route('/api/login', methods=['GET', 'POST'])
def login():
    form_data = MultiDict(request.get_json())
    form = LoginForm(form_data)
    if form.validate_on_submit():
        attempted_user = User.query.filter_by(username=form.username.data).first()
        if attempted_user and attempted_user.check_password_correction(attempted_password=form.password.data):
            login_user(attempted_user)
            return jsonify({'message': 'User logged in successfully'}), 200
        else:
            return jsonify({'errors': 'Username and password do not match! Please try again'}), 400


@app.route('/api/logout')
def logout():
    logout_user()
    return {'message': 'Logged out successfully'}
