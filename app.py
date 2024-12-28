from flask import Flask, flash, redirect, render_template, jsonify, request, session, g
from flask_session import Session
from helper import login_required
import os
import requests
import sqlite3
import time
from werkzeug.security import check_password_hash, generate_password_hash
from werkzeug.utils import secure_filename


# Configure application
app = Flask(__name__)

# Define the folder where uploaded files will be stored
# Make sure this folder exists or create it
app.config['UPLOADED_FILES'] = 'uploaded_files/'  # Define a folder to store uploaded files

# Ensure the folder exists
if not os.path.exists(app.config['UPLOADED_FILES']):
    os.makedirs(app.config['UPLOADED_FILES'])

app.config['FLASH_MESS'] = ""

# Configure session to use filesystem (instead of signed cookies)
app.config["SESSION_PERMANENT"] = False
app.config["SESSION_TYPE"] = "filesystem"
Session(app)


@app.before_request
def before_request():
    """Connect to the database before each request."""
    g.db = sqlite3.connect('database.db')
    g.db.row_factory = sqlite3.Row      # This allows you to access columns by name
    create_tables_if_not_exists()       # Check and create tables if they don't exist


@app.teardown_request
def teardown_request(exception):
    """Close the database connection after each request."""
    db = getattr(g, 'db', None)
    if db is not None:
        db.close()


@app.after_request
def after_request(response):
    """Ensure responses aren't cached"""
    response.headers["Cache-Control"] = "no-cache, no-store, must-revalidate"
    response.headers["Expires"] = 0
    response.headers["Pragma"] = "no-cache"
    return response


def create_tables_if_not_exists():
    """Check if the required tables exist, and create them if not."""
    users = g.db.execute(
        '''SELECT name FROM sqlite_master WHERE type='table' AND name=?''', ("users",)
                        ).fetchall()
    anime_names = g.db.execute(
        '''SELECT name FROM sqlite_master WHERE type='table' AND name=?''', ("animes",)
                        ).fetchall()

    # create database tables if not exist
    if not users :
        g.db.execute(
            '''CREATE TABLE users (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    username TEXT UNIQUE,
                    hash TEXT UNIQUE
                    )''')
    if not anime_names:
        g.db.execute(
            '''CREATE TABLE animes (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    user_id INTEGER NOT NULL,
                    anime_id INTEGER NOT NULL,
                    anime_title TEXT NOT NULL,
                    alt_title TEXT NOT NULL,
                    FOREIGN KEY(user_id) REFERENCES users(id)
                    )''')
    g.db.commit()  # Commit the change to the database


@app.route("/register", methods=["GET", "POST"])
def register():                                 # <<---------DONE-----
    """Register user"""
    if request.method == "GET":
        return render_template("register.html")

    else:
        username = request.form.get("username")
        password = request.form.get("password")
        confirmation = request.form.get("confirmation")

        # Query the database to get all existing usernames
        users = g.db.execute("SELECT username FROM users").fetchall()  # Fetch all rows

        # Check if user inputs are blank
        if not username or not password or not confirmation:
            flash("User Input Is Blank", "error")
            return redirect("/register")

        # Check if password matches confirmation
        if password != confirmation:
            flash("Password Does Not Match", "error")
            return redirect("/register")

        # Check if username is already taken
        for user in users:
            if username == user["username"]:
                flash("Username Already Taken", "error")
                return redirect("/register")

        # Generate a hashed password using the scrypt method
        hashpassword = generate_password_hash(password, method='scrypt', salt_length=16)

        # Insert the new user into the database
        g.db.execute(
            "INSERT INTO users (username, hash) VALUES (?, ?)", (username, hashpassword)
            )
        g.db.commit()  # Commit the change to the database

        # Redirect to the login page
        return redirect("/login")

@app.route("/login", methods=["GET", "POST"])
def login():                                            # <<--------------done
    """Log user in"""
    # Forget any user_id
    session.clear()
    
    # User reached route via POST (as by submitting a form via POST)
    if request.method == "POST":
        # Ensure username was submitted
        if request.form.get("username") == '':
            app.config['FLASH_MESS'] = "Must Provide Username"
            return redirect("/login")

        # Ensure password was submitted
        elif request.form.get("password") == '':
            app.config['FLASH_MESS'] = "Must Provide Password"
            return redirect("/login")

        # Query database for username
        rows = g.db.execute(
            "SELECT * FROM users WHERE username = ?", (request.form.get("username"),)
            ).fetchall()

        # Ensure username exists and password is correct
        if len(rows) != 1 or not check_password_hash(rows[0]["hash"], request.form.get("password")):
            app.config['FLASH_MESS'] = "Invalid Username And/Or Password"
            return redirect("/login")

        # Remember which user has logged in
        session["user_id"] = rows[0]["id"]

        # Redirect user to home page
        return redirect("/")

    # User reached route via GET (as by clicking a link or via redirect)
    else:
        if app.config['FLASH_MESS']:
            flash(f"{app.config['FLASH_MESS']}", "error")
            app.config['FLASH_MESS'] = ""
        return render_template("login.html")


@app.route("/logout")
def logout():
    """Log user out"""
    # Forget any user_id
    session.clear()

    # Redirect user to login form
    return redirect("/")


@app.route("/", methods=["GET", "POST"])
@login_required
def index():
    if not session.get("user_id"):
        return render_template("login.html")
    return render_template("index.html")


def fetch_with_name(qname, snumber):
    # API endpoint with all fields included
    url = f"https://api.myanimelist.net/v2/anime?q={qname}&limit={snumber}&fields=title,main_picture,alternative_titles,start_date,end_date,synopsis,mean,rank,popularity,num_list_users,num_scoring_users,status,genres,num_episodes,start_season,rating,studios,media_type"

    # Headers with your Client ID
    headers = {
        "X-MAL-CLIENT-ID": "4268486705dc98087214ea6c1f279480"
    }

    # Send the GET request
    response = requests.get(url, headers=headers)

    # search results (formatted as JSON)
    result = response.json()
    return result


def fetch_with_id(anime_id):
    # API endpoint with all fields included
    url = f"https://api.myanimelist.net/v2/anime/{anime_id}?fields=title,main_picture,alternative_titles,start_date,end_date,synopsis,mean,rank,popularity,num_list_users,num_scoring_users,status,genres,num_episodes,start_season,rating,studios,media_type"

    # Headers with your Client ID
    headers = {
        "X-MAL-CLIENT-ID": "4268486705dc98087214ea6c1f279480"
    }

    # Send the GET request
    response = requests.get(url, headers=headers)

    # search results (formatted as JSON)
    result = response.json()
    return result


def api_search(fetch_type, anime_id, sname, snumber):
    # if anime name is too long
    if "," in sname and len(sname) > 62:
        name = sname.split(",", 1)[0]
        qname = name.replace(" ","%20")
    else:
        name = sname
        qname = sname.replace(" ","%20")

    # check if snumber valid and <= 10
    try:
        if 1 > int(snumber) > 10:
            snumber = "5"
    except ValueError:
        snumber = "5"

    if fetch_type == 0:
        result = fetch_with_name(qname, snumber)
        # check if search was successful and the is a result
        if result.get("data", "No Data") == "No Data":
            result_list = ["No Data"]
            return result_list

    else :
        result = fetch_with_id(anime_id)
        alternative_titles = [result.get("alternative_titles", "No Title")]
        if alternative_titles != "No Title":
            alt_title = alternative_titles[0].get("en", "No Title")
        genres_list = result.get("genres", "No Genres")
        if genres_list != "No Genres":
            genres = [genre["name"] for genre in genres_list]
        
        result_data = [{f"result": {
            "id": result.get("id"), 
            "title": result.get("title", "No Title") ,
            "picture": result["main_picture"].get("large", "No Image") ,
            "alt_title":  alt_title or "No Title",
            "start_date": result.get("start_date", "No Start Date") ,
            "end_date": result.get("end_date", "No End Date") ,
            "synopsis": result.get("synopsis", "No Synopsis") ,
            "mean": result.get("mean", "No Mean") ,
            "rank": result.get("rank", "No Rank") ,
            "popularity": result.get("popularity", "No Popularity") ,
            "num_list_users": result.get("num_list_users", "No List Users") ,
            "num_scoring_users": result.get("num_scoring_users", "No Scoring Users") ,
            "status": result.get("status", "No Status").replace("_", " ").title() ,
            "genres": genres or ["No Genres"],
            "num_episodes": result.get("num_episodes", "No Number of Episodes") ,
            "start_season": result.get("start_season", "No Start Season") ,
            "rating": result.get("rating", "No Rating").replace("_", " ").title() ,
            "studios": result.get("studios", "No studios"), 
            "media_type": result.get("media_type", "No Media Type").replace("_", " ").title()
            }}]
        return result_data
        
    result_list = []

    for i in range(len(result["data"])):
        id = result["data"][i]["node"].get("id")
        title = result["data"][i]["node"].get("title", "No Title")
        
        main_picture = result["data"][i]["node"].get("main_picture", "No Image")
        if main_picture != "No Image":
            picture = main_picture.get("large", "No Image")
        
        alternative_titles = [result["data"][i]["node"].get("alternative_titles", "No Title")]
        if alternative_titles != "No Title":
            alt_title = alternative_titles[0].get("en", "No Title")
        
        start_date = result["data"][i]["node"].get("start_date", "No Start Date")
        end_date = result["data"][i]["node"].get("end_date", "No End Date")
        synopsis = result["data"][i]["node"].get("synopsis", "No Synopsis")
        mean = result["data"][i]["node"].get("mean", "No Mean")
        rank = result["data"][i]["node"].get("rank", "No Rank")
        popularity = result["data"][i]["node"].get("popularity", "No Popularity")
        num_list_users = result["data"][i]["node"].get("num_list_users", "No List Users")
        num_scoring_users = result["data"][i]["node"].get("num_scoring_users", "No Scoring Users")
        status = result["data"][i]["node"].get("status", "No Status").replace("_", " ").title()
        
        genres_list = result["data"][i]["node"].get("genres", "No Genres")
        if genres_list != "No Genres":
            genres = [genre["name"] for genre in genres_list]
        
        num_episodes = result["data"][i]["node"].get("num_episodes", "No Number of Episodes")
        start_season = result["data"][i]["node"].get("start_season", "No Start Season")
        rating = result["data"][i]["node"].get("rating", "No Rating").replace("_", " ").title()
        studios = result["data"][i]["node"].get("studios", "No studios")
        media_type = result["data"][i]["node"].get("media_type", "No Media Type").replace("_", " ").title()

        result_data = {f"result": {
            "id": id, "title": title ,"picture": picture ,"alt_title": alt_title ,"start_date": start_date ,
            "end_date": end_date ,"synopsis": synopsis ,"mean": mean ,"rank": rank ,
            "popularity": popularity ,"num_list_users": num_list_users ,"num_scoring_users": num_scoring_users ,
            "status": status ,"genres": genres ,"num_episodes": num_episodes ,"start_season": start_season ,
            "rating": rating ,"studios": studios, "media_type": media_type
            }}

        result_list.append(result_data)
    # result_list is the results of 1 search (-> list of dic) 
    return result_list          # EX: -> result_list = [{"result": {}}, {"result": {}},]


@app.route("/search", methods=["POST"])
def search():
    sname = request.form.get("sname")
    snumber = request.form.get("snumber")
    if not sname:
        if not session.get("user_id"):
            flash("Search Input Can Not Be Empty", "error")
            return render_template("login.html")
        
        flash("Search Input Can Not Be Empty", "error")
        return render_template("index.html")
    try:
        if not snumber.isdigit():
            snumber = "5"
    except Exception:
        snumber = "5"
    if session.get("user_id"):
        user = "user"
    
    else:
        user = None

    search_data = api_search(0, None, sname, snumber)
    return render_template("search.html", search_data = search_data, sname = sname, user = user)


@app.route("/guest", methods=["GET"])
def guest():
    return render_template("guest.html")


# Read anime names from the text file
def read_txt_file(file_path: str):
    try:
        with open(file_path, 'r') as file:
            anime_list = [line.strip() for line in file.readlines() if line != "\n"]
        return anime_list

    except FileNotFoundError:
        return None


def process_list(anime_list: list):
    all_names_data = []
    for i in range(len(anime_list)):
        anime_data = api_search(0, 0, anime_list[i], "5")
        all_names_data.append({"data": anime_data})
        time.sleep(2)  # Be polite to the API and avoid rate-limiting
    return all_names_data


@app.route("/file_search", methods=["GET", "POST"])
@login_required
def file_search():
    if request.method == "GET":
        return render_template("file_search.html")

    else:
        uploaded_file = request.files["filename"]

        if not uploaded_file :
            flash("Please Choose a Valid txt File!", "error")
            return redirect("/file_search")

        # validate the extension file
        ALLOWED_EXTENSIONS = {"txt"}
        CHECK_VALID = '.' in uploaded_file.filename and uploaded_file.filename.rsplit(".", 1)[1].lower() in ALLOWED_EXTENSIONS

        # Check if a file is selected
        if uploaded_file.filename != '' and CHECK_VALID:
            # ensure that the filenames are safe and do not contain any malicious or illegal characters.
            safe_filename = secure_filename(uploaded_file.filename)

            # Save the file to the designated folder
            file_path = os.path.join(app.config['UPLOADED_FILES'], safe_filename)
            uploaded_file.save(file_path)

            file_data = read_txt_file(file_path)
            try:
                alldata_intxtfile = process_list(file_data)
            except Exception:
                flash("Error Please Try Again", "error")
                return redirect("/file_search")

            # remove the file after processing
            os.remove(file_path)
            return render_template("result_search.html", list_data = file_data, all_data_sent = alldata_intxtfile)

        else:
            flash(f"File '{uploaded_file.filename}' Not Text File!, Please Choose Valid Text file (.txt)!", "error")
            return redirect("/file_search")


@app.route("/text_search", methods=["GET", "POST"])
@login_required
def text_search():
    if request.method == "GET":
        return render_template("text_search.html")
    else:
        textarea = request.form.get("textinputarea")
        inputlist = [name.strip() for name in textarea.split("\n") if name.strip() != ""]
        
        try:
            alldata_inputlist = process_list(inputlist)
        except Exception:
            flash("Error Please Try Again", "error")
            return redirect("/text_search")

        return render_template("result_search.html", list_data = inputlist, all_data_sent = alldata_inputlist)


# Next add a button to save anime name in database file in result_search.html
@app.route("/add_name", methods=["POST"])
@login_required
def add_name():
    data = request.json
    anime_id = int(data.get('anime_id'))                    # wanted id
    anime_title = data.get('anime_title')                   # wanted title
    alt_title = data.get('alt_title')                       # wanted alt_title

    # Query the database to get all existing animes 
    animes_tuples = g.db.execute(
        "SELECT anime_id FROM animes WHERE user_id = ?", (session.get("user_id"),)
        ).fetchall()  # Fetch all rows
    all_animes_ids = [name[0] for name in animes_tuples]

    # if there is NO data of animes table in the database 
    if not all_animes_ids:
        # Insert the new data to animes table
        g.db.execute(
            "INSERT INTO animes (user_id, anime_id, anime_title, alt_title) VALUES (?, ?, ?, ?)", (
                session.get("user_id"), anime_id, anime_title, alt_title)
            )
        g.db.commit()  # Commit the change to the database
        
        return jsonify({"message": f"Anime With Title '{anime_title}' Added", "type": "alert alert-success mb-0 text-center"}), 200
    
    # if there is DATA in animes table
    else:
        if anime_id not in all_animes_ids:
            g.db.execute(
                "INSERT INTO animes (user_id, anime_id, anime_title, alt_title) VALUES (?, ?, ?, ?)", (
                    session.get("user_id"), anime_id, anime_title, alt_title)
                )
            g.db.commit()  # Commit the change to the database

            return jsonify({"message": f"Anime With Title '{anime_title}' Added", "type": "alert alert-success mb-0 text-center"}), 200
        else:
            return jsonify({"message": f"Anime With Title '{anime_title}' Already Exist", "type": "alert alert-warning mb-0 text-center"}), 200


# make view data from databae function
@app.route("/view_names", methods=["GET"])
@login_required
def view_names():
    anime_list_db = g.db.execute(
        "SELECT anime_id FROM animes WHERE user_id = ?", (session.get("user_id"),)
        ).fetchall()
    sql_anime_list = [name[0] for name in anime_list_db]
    if not sql_anime_list:
        return render_template("search.html", view_result = "view_result", search_data = "No Animes Saved", remove_name = "remove" , user = "user")
    else:
        alldata_sqllist = []            # [[{"result": "value"}], [{"result": "value"}], [{"result": "value"}], ]
        try:
            for anime_id in sql_anime_list:
                anime_data = api_search(1, anime_id, "", "5")
                alldata_sqllist.append(anime_data[0])

        except Exception as e:
            flash(f"Error Please Try Again, {e}", "error")
            return redirect("/")
        
        return render_template("search.html", view_result = "view_result", search_data = alldata_sqllist, remove_name = "remove" , user = "user")


# last make a function to remove anime from database
@app.route("/remove_name", methods=["POST"])
@login_required
def remove_name():
    anime_id = int(request.form.get('anime_id'))
    anime_title = request.form.get('anime_title')

    # delete anime data from animes table
    g.db.execute(
        "DELETE FROM animes WHERE user_id = ? AND anime_id = ?", (
            session.get("user_id"), anime_id,)
        )
    g.db.commit()  # Commit the change to the database
    flash(f"Anime With Title '{anime_title}' Has Been Removed", "info")
    return redirect("/view_names")


# maybe add a function to remove user from database
@app.route("/settings", methods=["GET", "POST"])
@login_required
def settings():
    if request.method == "GET":
        return render_template("settings.html")
    
    else:
        delete_user = request.form.get("confirmusername")
        # Query database for username
        user_name = g.db.execute(
            "SELECT username FROM users WHERE id = ?", (session["user_id"],)
            ).fetchall()

        if user_name[0][0].upper() == delete_user:
            g.db.execute(
                "DELETE FROM animes WHERE user_id = ?", (session["user_id"],)
                ).fetchall()
            g.db.execute(
                "DELETE FROM users WHERE id = ?", (session["user_id"],)
                ).fetchall()
            g.db.commit()  # Commit the change to the database

            session.clear()
            return redirect("/login")
        else:
            flash("User Name Not Correct !", "info")
            return redirect("/settings")


# THE END