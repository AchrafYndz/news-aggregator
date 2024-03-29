import React, {useEffect, useState, useRef} from 'react';
import InfiniteScroll from "react-infinite-scroll-component";
import axios from "axios";
import moment from "moment/moment";
import {Simulate} from "react-dom/test-utils";
import error = Simulate.error;
import RenderArticles from "./renderArticles"
import * as Loader from "react-loader-spinner";
import {usePromiseTracker} from "react-promise-tracker";
import {trackPromise} from 'react-promise-tracker';



const Scroller = ({ sort, labels, query, excluded }: { sort: string; labels: string[]; query: string; excluded: string[] }) => {
    const [articles, setArticles] = useState<any[]>([]);
    const [shownArticles, setShownArticles] = useState<any[]>([]);
    const [skip, setSkip] = useState<number>(0);
    const hasMore = useRef(true);

    const {promiseInProgress} = usePromiseTracker();

    useEffect(() => {
        setSkip(0);
        hasMore.current = true;
        updateShownArticles(true);
    }, [sort, labels, query, excluded]);

    const fetchDataApi = async (reset: boolean = false) => {
        // let offsetValue = articles.length;
        let offsetValue = skip;
        
        if (reset) {
            offsetValue = 0;
        }
        const response = await trackPromise( axios.get(
            '/api/articles', {
                params: {
                    offset: offsetValue,
                    sort: sort,
                    searchQuery: query,
                    labels: labels,
                    exclude: excluded.map((pair : any) => pair.value)
                }
            }
        ))
        const groups = await Promise.all(response.data.map(async (article: any) => {
        const similarArticles = await axios.get(`/api/similarity/`, {
                params: {
                    article_link: article["link"]
                }
            }
        );
        return {
            article,
            similarArticles: similarArticles.data.filter((link: any) => link !== article.link)
        };
        }));
        const newData = groups.map((group) => ({
                ...group.article,
                similarArticles: group.similarArticles
            }));
        if (! reset) {
            setSkip(prevState => prevState+100);
        }
        if (response.data.length > 0) {
            
            if (reset) {
                setArticles((prevApiArticles: any[]) => newData)
            } else {
                setArticles((prevApiArticles: any[]) => prevApiArticles.concat(newData))
            }
        } else if (response.data.length === 0 && reset) {
             setArticles((prevApiArticles: any[]) => [])
        } else{
            hasMore.current = false;
        }
    };

    const updateShownArticles = (reset: boolean = false) => {
        if (reset) {
            fetchDataApi(true);
        } else if (shownArticles.length == articles.length && hasMore.current) {
            fetchDataApi(false);
        }  else if (articles.length > shownArticles.length + 10) {
            setShownArticles(prevState => articles.slice(0, prevState.length + 10));
        } else {
            setShownArticles(prevState => articles.slice());
        }
    }

    useEffect(() => {
        if (articles.length <= 100) {
            if (articles.length < 10) {
                setShownArticles(prevState => articles.slice());
            } else {
                setShownArticles(prevState => articles.slice(0, prevState.length+10));
            }
        } else {
            if (hasMore.current) {
                setShownArticles(prevState => articles.slice(0, prevState.length + 10));
            } else if (articles.length % 100 < 10) {
                setShownArticles(prevState => articles.slice());
            } else {
                setShownArticles(prevState => articles.slice(0, prevState.length + 10));
            }
        }
    }, [articles])

    return (
        <InfiniteScroll
            dataLength={shownArticles.length}
            next={updateShownArticles}
            hasMore={hasMore.current}
            loader={
            <div>
-                        <div
                            style={{
                                width: "100%",
                                height: "100",
                                display: "flex",
                                justifyContent: "center",
                                alignItems: "center"
                            }}
                        >
                            <Loader.ThreeDots color="#284B63" height="100" width="100"/>
                        </div>
-                </div>
            }
            endMessage={
                <p style={{textAlign: 'center'}}>
                    <b>End of feed</b>
                </p>
            }
        >
             {promiseInProgress &&
                        <div
                            style={{
                                width: "100%",
                                height: "100",
                                display: "flex",
                                justifyContent: "center",
                                alignItems: "center"
                            }}
                        >
                            <Loader.ThreeDots color="#284B63" height="100" width="100"/>
                        </div>
                    }
            <RenderArticles articles={shownArticles} />
        </InfiniteScroll>
    );
};

export default Scroller;
