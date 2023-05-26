from datetime import datetime, timedelta
from src.server.resemblance.resemblance import get_resemblance, get_resemblance_object
from src.server.database import Article, db, TF_IDF, History
from src.server.ConnectDB import ConnectDB
from sqlalchemy import desc, cast, Date, or_

from src.server.link_articles import create_source_document, from_same_site

ConnectDB = ConnectDB(db)
#
def get_similar_articles(article_link):
    # Retrieve all rows in the tf_idf table where the given article ID is present
    rows = db.session.query(TF_IDF).filter(
        or_(TF_IDF.article1 == article_link, TF_IDF.article2 == article_link)
    ).all()

    # Create a set of unique article IDs that are similar to the given article ID
    similar_articles = set()
    for row in rows:
        if row.article1 == article_link:
            similar_articles.add(row.article2)
        else:
            similar_articles.add(row.article1)
    return similar_articles

class ArticlesFetcher:
    def __init__(self):
        self.article_links = []

    def create_articles(self, skip, stop, db_articles):
        if skip == 0:
            self.article_links = []


        articles = []
        for i in range(skip, stop):
            db_article = db_articles[i]

            # Create a set of unique article IDs that are similar to the given article ID
            similar_articles = get_similar_articles(db_article.link)

            add = not any([similar_article for similar_article in similar_articles if similar_article in self.article_links])


            if add:
                self.article_links.append(db_article.link)

                article = {
                    "title": db_article.title,
                    "description": db_article.description,
                    "image": db_article.image,
                    "link": db_article.link,
                    "pub_date": db_article.pub_date
                }

                articles.append(article)

        return articles

    def fetch_recent(self, skip = 0):
        db_articles = Article.query.order_by(desc(Article.pub_date)).all()

        last_index = len(db_articles) - 1

        skip10 = skip + 10

        stop = last_index

        if skip10 < last_index:
            stop = skip10

        if skip > last_index:
            print("reached the end")
            return []

        return self.create_articles( skip, stop, db_articles)

    def fetch_popular(self, skip = 0):
        seven_days_ago = datetime.now() - timedelta(days=7)
        db_articles = Article.query.filter(cast(Article.pub_date, Date) >= seven_days_ago.date()).order_by(desc(Article.views)).all()

        last_index = len(db_articles) - 1

        skip10 = skip + 10

        if skip10 > last_index:
            return self.fetch_recent(skip - 10)

        return self.create_articles(skip, skip10, db_articles)

    def fetch_recommended(self, user_id, skip=0):
        history_objs: list[History] =  History.query.filter(History.user_id == user_id).all()

        all_articles = Article.query.all()
        clicked_articles = [history_obj.article_link for history_obj in history_objs]

        # Loop over all articles
        query_result = []
        for article_obj in all_articles:
            text = article_obj.title + " " + article_obj.description
            text = text.replace("\n", "")
            text = ''.join([i if (i.isalnum()) else ' ' for i in text])  # Strip all special characters
            text += '.'
            query_result.append((text, article_obj.link))

        create_source_document(query_result)

        res_obj = get_resemblance_object('.records')

        duplicates_set = set()

        # Loop over the articles in history
        for link in clicked_articles:
            article = Article.query.filter(Article.link == link).all()[0]
            with open(".current_record", 'w') as file:
                text = article.title + " " + article.description
                text = text.replace("\n", "")
                text = ''.join([i if (i.isalnum()) else ' ' for i in text])  # Strip all special characters
                text += '.'
                file.write(text)
                file.write('\n')

            res_dict = get_resemblance(res_obj, '.current_record')
            for i in range(len(res_dict)):
                if res_dict[i] > 0.05:
                    if article.link != query_result[i][1]:
                        if not from_same_site(article.link, query_result[i][1]):
                            duplicates_set.add(query_result[i][1])
        db_articles = [Article.query.filter(Article.link == duplicate_link).first() for duplicate_link in duplicates_set]

        last_index = len(db_articles) - 1

        skip10 = skip + 10

        if skip10 > last_index:
            return self.fetch_recent(skip - 10)

        return self.create_articles(skip, skip10, db_articles)
