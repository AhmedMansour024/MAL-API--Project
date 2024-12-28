# _MAL API Project_

## Video Demo for the Project:  [Watch Here](https://youtu.be/MH-EPgqFNe4)

## Description

This is a Web application project made with flask.

project libraries:

1. Flask
2. Flask-Session
3. Werkzeug
4. requests

the project has 4 folders:

1. **flask_session**: remember users.

2. **static**: contain any static files like photos or css files or js files.

3. **templates**: contain all html files.

4. **uploaded_files**: its used to store all uploaded files from users.

and has 4 files:

1. **app.py**: main application file.
2. **database.db**: database file that store all users data.
3. **helper.py**: python file that contain separate functions that used in the app.py file.
4. **requirements.txt**: contain all libraries required for app.py

in the **templates** folder:

1. **file_search.html**
2. **guest.html**
3. **index.html**
4. **layout.html**
5. **login.html**
6. **register.html**
7. **result_search.html**
8. **search.html**
9. **settings.html**
10. **text_search.html**

Functions in **app.py**:

1. **create_tables_if_not_exists**: it create all required tables in the database file if its not exist.
2. **register**: its used to create new user and save it in the database.
3. **login**: its used to log in the user into his/her account after checking for the correct username and password.
4. **logout**: used to clear the saved session (cookies) and log the user out.
5. **index**: used to display the home page for the user.
6. **fetch_with_name**: used to fetch anime data from MyAnimeList API using anime name.
7. **fetch_with_id**: used to fetch anime data from MyAnimeList API using anime id.
8. **api_search**: used to call fetch_with_name or fetch_with_id functions when needed and process the returned data from these function to easily to use in html files to be displayed also return one anime result.
9. **search**: a function called when the user use **single search** and display the result using **search.html** file.
10. **guest**: used to display the guest page.
11. **read_txt_file**: used to process the **.txt** files and return a list of all the rows in the text file.
12. **process_list**: used to process a list of animes and call **api_search** function for every anime in the list.
13. **file_search**: used to receive the uploaded **(.txt)** files and make sure the file is safe and does not contain any any malicious or illegal characters, and convert the txt file to a list of animes that also being processed by **process_list** function.
14. **text_search**: used to receive the group text user imputed and call **process_list** to convert it to a list of animes.
15. **add_name**: called when user pressed on add button when resluts was displayed to add the anime data that associated with to the database file.
16. **view_names**: used to display all saved animes in the database file by calling **api_search**
using the database list.
17. **remove_name**: used to remove the anime associated with from the database.
18. **settings**: used to **_DELETE_** all user saved data and **_DELETE_** its account.
