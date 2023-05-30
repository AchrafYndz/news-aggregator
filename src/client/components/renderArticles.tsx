import React, {useEffect, useState, useRef} from 'react';
import styles from "./Article.module.scss";
import moment from "moment";
import axios from "axios";
import Cookies from "js-cookie";
import { ShareButton } from './ShareButton';


function RenderArticles({ articles }: {articles: any}) {
    const [username, setUsername] = useState<string | null>(null);

    useEffect(() => {
        axios.get('/api/@me', {
            headers: {
                'Content-Type': 'application/json'
            }
        })
            .then(response => {
                if (response.status === 200) {
                    setUsername(response.data.username)
                } else {
                    console.log("Not logged in")
                }
            })
            .catch(error => {
                console.log(error)
            })
    }, []);

    useEffect(() => {
        console.log("new articles")
        console.log(articles)
    },[articles])

    const TrackHistory = (link: string) => {
        const linkData = {
            link: link
        }
        axios.put('/api/articles/view', linkData, {
            headers: {
                'Content-Type': 'application/json'
            }
        }).catch(error => {
            console.log(error)
        })
        if (username !== null) {
            axios.post('/api/history', linkData, {
                headers: {
                    'Content-Type': 'application/json'
                }
            }).catch(error => {
                console.log(error)
            })
        } else {
            if (!Cookies.get("history_index")) {
                Cookies.set("history_index", "0");
            }
            let AddCookie: boolean = false;
            if (Cookies.get("history_" + Cookies.get("history_index")) === undefined) {
                let array: string[] = []
                Cookies.set("history_" + Cookies.get("history_index"), JSON.stringify(array));
            }
            let cookieValue = Cookies.get("history_" + Cookies.get("history_index"))
            if (typeof cookieValue === "string") {
                let Cookie_history = JSON.parse(cookieValue);
                Cookie_history.push(link);
                if (Cookie_history.length > 100) {
                    AddCookie = true
                }
                Cookies.set("history_" + Cookies.get("history_index"), JSON.stringify(Cookie_history));
            }
            let indexValue = Cookies.get("history_index")
            if (typeof indexValue === "string" && AddCookie) {
                let newIndex: string = indexValue + 1;
                Cookies.set("history_index", newIndex);
            }
        }
    };


    return (
            <div className={styles.articles}>
                {   articles.map(({link, image, title, description, pub_date, similarArticles}: {
                    link: any,
                    title: any,
                    image: any,
                    description: any,
                    pub_date: any,
                    similarArticles: any
                }) => {
                    return (
                        <div key={link} onClick={() => TrackHistory(link)} className={styles.article}>
                            <a href={link} target={"blank"} className={styles.article_link}>
                                <img className={styles.favicon} height="16" alt={"favicon"} width="16"
                                     src={'http://www.google.com/s2/favicons?domain=' + link}/>
                                <ShareButton url={link} />
                                <img src={image !== null ? image : 'img.png'} alt={title}/>
                                <h2>{title}</h2>
                                <p className={styles.description}>{description}</p>
                                <p className={styles.time_ago}>{moment(pub_date).fromNow()}</p>
                            </a>
                            {similarArticles.length > 0 && (
                                <p>
                                    Also published by:{' '}
                                    <div id={styles.published_by_container}>
                                        {similarArticles.map((similarArticleId: any) => (
                                            <React.Fragment key={similarArticleId}>
                                                <a href={`${similarArticleId}`} target="_blank"
                                                   rel="noopener noreferrer" className={styles.published_by}>
                                                    <img
                                                        src={'http://www.google.com/s2/favicons?domain=' + similarArticleId}
                                                        alt='favicon' className={styles.favicon}/>
                                                </a>
                                            </React.Fragment>
                                        ))}
                                    </div>

                                </p>
                            )}
                        </div>
                    )
                })}
            </div>
    )
}

export default RenderArticles;
