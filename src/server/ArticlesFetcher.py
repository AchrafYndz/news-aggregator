from src.server.database import Article,db
from src.server.ConnectDB import ConnectDB
from sqlalchemy import desc

ConnectDB=ConnectDB(db)

def fetch():
    db_articles = Article.query.order_by(desc(Article.pub_date)).all()

    articles = []
    # Loop through each article in the feed
    for db_article in db_articles:
        article = {
            "title": db_article.title,
            "description": db_article.description,
            "image": db_article.image,
            "link": db_article.link,
            "pub_date": db_article.pub_date
        }

        articles.append(article)

    return articles




if __name__ == "__main__":
    fetch()
