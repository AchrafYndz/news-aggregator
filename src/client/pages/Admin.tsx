import React from "react";
import Header from "../components/Header";
import styles from "../components/Admin.module.scss";


export default function Admin() {
    return (
        <div className={styles.forms}>
            <div className={styles.form}>
                <h1>Add new RSS Feed</h1>
                <form method="post">
                    <label>Feed URL:</label>
                    <input type="text" id="feed_url" name="feed_url" required/>
                    <br/>
                    <label>Feed Name:</label>
                    <input type="text" id="feed_name" name="feed_name" required/>
                    <br/>
                    <div className={styles.buttons}>
                        <input className={styles.button + ' ' + styles.add} type="submit" value="Add Feed"/>
                        <input className={styles.button + ' ' + styles.remove} type="submit" value="Delete Feed"/>
                    </div>
                </form>
            </div>
            <div className={styles.form}>
                <h1>Add new Admin</h1>
                <form method="post">
                    <label>Username:</label>
                    <input type="text" id="username" name="username" required/>
                    <br/>
                    <label>Password:</label>
                    <input type="password" id="password" name="password" required/>
                    <br/>
                    <div className={styles.buttons}>
                        <input className={styles.button + ' ' + styles.add} type="submit" value="Add Admin"/>
                        <input className={styles.button + ' ' + styles.remove} type="submit" value="Delete Admin"/>
                    </div>
                </form>
            </div>
        </div>
    );
}