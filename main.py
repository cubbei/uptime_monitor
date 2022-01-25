import flask
import asyncio
import datetime
from requests import get, Response
from requests.exceptions import ConnectionError
import sqlite3
import multiprocessing as mp


app = flask.Flask(__name__)




def db_init():
    query = """
    CREATE TABLE IF NOT EXISTS site_stats (
        site TEXT NULL,
        check_time DATETIME,
        available BOOL
    )"""
    run_query(query)
    query = """
    CREATE TABLE IF NOT EXISTS site_list (
        site TEXT NULL,
        active BOOL
    )"""
    run_query(query)

def run_query(query: str):
    # print(f"running query: `{query}`")
    with sqlite3.connect('uptime.db') as db_conn:
        db_curs = db_conn.cursor()
        db_curs.execute(query)
        db_conn.commit()
        
def get_data(query: str):
    with sqlite3.connect('uptime.db') as db_conn:
        db_curs = db_conn.cursor()
        db_curs.execute(query)
        dt = db_curs.fetchall()
        return dt

def get_timestamp():
    st = datetime.datetime.now()
    return st.strftime("%Y-%m-%d %H:%M:%S.%f")
    


async def checksites():
    query = "SELECT site from site_list where active = 1"
    s_query = "INSERT INTO site_stats (site, check_time, available) VALUES ('{site}', '{check_time}', 1);"
    f_query = "INSERT INTO site_stats (site, check_time, available) VALUES ('{site}', '{check_time}', 0);"
    sites = get_data(query)
    print(f"Checking availability of {len(sites)} sites... standby...")
    if len(sites) < 1:
        print("no sites returned.")
        return
    for site in sites:
        site = site[0]
        print(f"Checking status of site '{site}' at {get_timestamp()} | ", end="")
        try:
            res: Response = get(site, timeout=2, headers={"User-Agent": "uptime_check - local check for connectivity to core internet services."})
            if res.status_code < 400:
                run_query(s_query.format(**{"site": site, "check_time": get_timestamp()}))
                print(" Status: OK")
            else:
                run_query(f_query.format(**{"site": site, "check_time": get_timestamp()}))
                print(" Status: Unreachable")
        except (TimeoutError, ConnectionError):
            print(" Status: Unreachable")
            print(f"no connection to '{site}' could be made")
            run_query(f_query.format(**{"site": site, "check_time": get_timestamp()}))


async def site_checker():
    while True:
        loop = asyncio.get_event_loop()
        loop.create_task(checksites())
        await asyncio.sleep(20)

def run_site():
    db_init()
    app.run()

def run_checker():
    loop = asyncio.get_event_loop()
    loop.run_until_complete(site_checker())

@app.route("/")
def home():
    query = "SELECT site from site_list where active = 1"

    sites = get_data(query)
    
    site_message = ""
    site_boiler = ""
    
    if len(sites) < 1:
        site_message = "no sites."
    else:
        site_message = f"{len(sites)} sites."
        for site in sites:
            site = str(site[0])
            id = site.replace("https://","").replace("http://","").replace(".","-")
            site_boiler += f"""
            <div class="site-stats">
                <h4>Stats: <a href="{site}" target="_blank">{site.replace("http://","").replace("https://","")}</a></h4>
                <canvas id="{id}" width="800" height="400"></canvas>
                <br>
            <div>
            """
    with open("template.html", "r") as f:
        content = f.read()
        return content.replace("{site_message}", site_message).replace("{site_boiler}", site_boiler)


@app.route("/stats")
def stats():
    query = "SELECT site from site_list where active = 1"
    query_stat = "SELECT Count(CASE WHEN available = 1 then site END), Count(site), strftime ('%m-%d %H',check_time) FROM site_stats WHERE site = '{site}' GROUP BY strftime ('%m-%d %H',check_time)"

    sites = get_data(query)
    print(f"Checking stats for {len(sites)} sites... standby...")
    if len(sites) < 1:
        print("no sites returned.")
        return
    return_data = {}
    for site in sites:
        site = site[0]
        data = get_data(query_stat.format(**{"site": site}))
        
        labels = []
        dataset = []
        colours = []
        bg_colours = []
        for row in data:
            labels.append(row[2])
            result = round(float(row[0])/row[1]*100, 2)
            dataset.append(result)
            colour = 'rgba(39, 174, 96, 1.0)' if result > 80 else 'rgba(243, 156, 18, 1.0)' if result > 60 else 'rgba(230, 126, 34, 1.0)' if result > 40 else 'rgba(231, 76, 60, 1.0)'
            colours.append(colour)
            bg_colours.append(colour.replace("1.0", "0.3"))
            

        out_data = {
            "labels": labels,
            "datasets": [{
                "label": f"Status for '{site}'",
                "data": dataset,
                "fill": True,
                "borderColor": colours,
                "backgroundColor": bg_colours,
                "borderWidth": 1
            }]
        }
        return_data[site] = out_data
    return return_data


@app.route("/chart.js")
def chartjs():
    with open("chart.js", "r") as f:
        content = f.read()
        return content

@app.route("/helpers.js")
def helpersjs():
    with open("helpers.js", "r") as f:
        content = f.read()
        return content

@app.route("/style.css")
def stylejs():
    with open("style.css", "r") as f:
        content = f.read()
        return content


@app.route("/site")
def add_site():
    site = flask.request.args["site"]
    print(f"adding site: '{site}' to the watch-list...")
    query = "INSERT INTO site_list (site, active) VALUES (\"{site}\", 1);"
    run_query(query.format(**{"site": site}))
    return flask.redirect("/")


if __name__ == "__main__":
    site = mp.Process(target=run_site)
    site_check = mp.Process(target=run_checker)
    site.start()
    site_check.start()
    site.join()
    site_check.join()