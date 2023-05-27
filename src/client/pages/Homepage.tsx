import React, {useEffect, useState} from "react";
import axios from "axios";
import styles from "../components/Article.module.scss";
import moment from "moment";
import {usePromiseTracker} from "react-promise-tracker";
import {trackPromise} from 'react-promise-tracker';
import * as Loader from "react-loader-spinner";
import {BsSearch} from "react-icons/bs";
import Carousel from "../components/Carousel";
import DropdownCheckbox from "../components/DropdownCheckbox";
import {MultiSelect} from "react-multi-select-component";
// @ts-ignore
import Cookies from "js-cookie";
import Scroller from "../components/InfiteScroller"

function toggleLabel(labelArray: string[], label: string): string[] {
  const index = labelArray.indexOf(label);

  if (index > -1) {
    // Label found, remove it
    labelArray.splice(index, 1);
  } else {
    // Label not found, add it
    labelArray.push(label);
  }
  console.log("toggle")
  return labelArray;
}

export default function Homepage() {
    const [username, setUsername] = useState<string | null>(null);
    const [searchQuery, setSearchQuery] = useState<string>("");
    const [searchResults, setSearchResults] = useState<any>(null);
    const [searchFilter, setSearchFilter] = useState<string>("Recency")
    const [selected, setSelected] = useState<any>([]);
    const [rssOptions, setRssOptions] = useState<any>([])
    const [finalQuery, setFinalQuery] = useState<string>("");
    const [sort, setSort] = useState<string>("Recency");
    const [activeLabels, setActiveLabels] = useState<string[]>([])

    useEffect(() => {

        const filter = Cookies.get('filter')

        const list = getRssList()

        console.log("LISSSSSSSSSSTT")
        console.log(list)

        setRssOptions(list)

        console.log("THIS IS OPRIONS RSS")
        console.log(rssOptions)


        if (filter != null) {
            setSearchFilter(filter)
        }



        const params = new URLSearchParams(window.location.search);
        const q = params.get('q');
        if (q) {
            setSearchQuery(q);
            handleSearch();
        }
    }, []);

    const {promiseInProgress} = usePromiseTracker();

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
    }, [])

    const handleFilter = (labelFilter: string) => {
        axios.get('/api/filter', {
            params: {
                label: labelFilter
            }
        })
            .then(response => {
                setSearchResults(response.data)
        })
            .catch(error => {
                console.log(error)
            })
    }

    const handleSearch = () => {
        trackPromise(
            axios.get('/api/search', {
                params: {
                    q: searchQuery
                }
            })
                .then(response => {
                    setSearchResults(response.data);
                })
                .catch(error => {
                    console.log(error)
                })
        )
    }

    const handleKeyDown = (event: any) => {
        if (event.key === 'Enter') {
            handleSearch()
        }
    };

    const TrackHistory = (link: string) => {
        const data = {
            link: link
        }
        axios.put('/api/articles/view', data, {
            headers: {
                'Content-Type': 'application/json'
            }
        }).catch(error => {
            console.log(error)
        })
        if (username !== null) {
            axios.post('/api/history', data, {
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
    }

    const getRssList = async () =>  {
        const API = await axios.get("api/rss");
        const responseData = API.data

        const dropDownValue = responseData.map((response : any) => ({
            "value" : response.id,
            "label" : response.name
        }))

        setRssOptions(dropDownValue)

    };



    const options = [

          { label: "Grapes 🍇", value: "grapes" },
          { label: "Mango 🥭", value: "mango" },
          { label: "Strawberry 🍓", value: "strawberry", disabled: true },
    ];

    const onChange = (event : any) => {

        const value = event.target.value;
        setSearchFilter(value);

        Cookies.set('filter', value);

        console.log("CHANGES");

        setSort(value);


        window.location.reload()



    };


    return (
        <div>
            <div className={styles.filteringContainer}>
                { /* Search Bar */}
                <div className={styles.searchBarContainer}>
                    <input type="text"
                           placeholder="Search"
                           value={searchQuery}
                           onChange={(e) =>
                               setSearchQuery(e.target.value)}
                           onKeyDown={handleKeyDown}
                           className={styles.searchBar}/>
                    <BsSearch className={styles.searchIcon}/>
                </div>
                { /* Placeholder Sort By */}
                <div className={styles.sortBy}>
                    <select value= {searchFilter} className={styles.sortBySelect} onChange={onChange}>
                        <option value="Recency">Recency</option>
                        <option value="Popularity">Popularity</option>
                    </select>
                </div>
                <div>
                    <MultiSelect options={rssOptions} value={selected} labelledBy={"Selected"} onChange={setSelected}/>
                </div>
            </div>
            { /* Search Animation */}
                <div>
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
                </div>
            { /* Labels */}
            <Carousel handleFilter={handleFilter}/>
            { /* Articles */}
            <div className={styles.container}>
                <Scroller labels={activeLabels} sort={sort} query={finalQuery}/>
            </div>
        </div>
    );
}
