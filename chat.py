from flask import Flask, request, Response
from datetime import datetime
from re import search
from mysql.connector import connect

config = {
    "host": "chat-db",
    "user": "root",
    "password": "example",
    "database": "chatDb",
    "port": 3306,
}

app = Flask(__name__)


def is_valid_room(room):
    return search(r"^general$|^[1-9]+\d*$", room)


def log_error():
    with open("logs.txt", "a+") as logs:
        logs.write(f"An error has occured. Time: {datetime.now()}\n")


def lobby_exists(lobby_id):
    try:
        cnx = connect(**config)
        cursor = cnx.cursor()
        cursor.execute("show tables;")
        table_name = f"lobby_{lobby_id}"

        result: bool
        for db_table in cursor:
            if db_table == table_name:
                result = True
        result = False

        return result
    except:
        log_error()
    finally:
        if cnx.is_connected():
            cursor.close()
            cnx.close()


def create_lobby(lobby_id):
    table = (f"CREATE TABLE `lobby_{lobby_id}` ("
             "`message_date` char(22) NOT NULL,"
             "`user_name` char(30) NOT NULL,"
             "`message_content` char(255) NOT NULL"
             ") ENGINE=InnoDB")

    try:
        cnx = connect(**config)
        cursor = cnx.cursor()
        cursor.execute(table)
    except:
        log_error()
    finally:
        if cnx.is_connected():
            cursor.close()
            cnx.close()


def read_lobby_messages(lobby_id):
    try:
        cnx = connect(**config)
        cursor = cnx.cursor()
        cursor.execute(f"SELECT * FROM lobby_{lobby_id}")

        messages = ""
        for (message_date, user_name, message_content) in cursor:
            messages += f"{message_date} {user_name}: {message_content}\n"

        return messages
    except:
        log_error()
    finally:
        if cnx.is_connected():
            cursor.close()
            cnx.close()


def write_message_to_lobby(lobby_id, user_name, message, formatted_time):
    try:
        cnx = connect(**config)

        entry_query = (f"INSERT INTO lobby_{lobby_id} "
                       "(message_date, user_name, message_content) "
                       f"VALUES ('{formatted_time}', '{user_name}', '{message}')")

        cursor = cnx.cursor()
        cursor.execute(entry_query)

        cnx.commit()
        return True
    except:
        log_error()
        return False
    finally:
        if cnx.is_connected():
            cursor.close()
            cnx.close()


@app.route("/<room>")
def get_lobby(room):
    if not is_valid_room(room):
        return Response(status=404)

    if not lobby_exists(room):
        create_lobby(room)

    with open("index.html") as index:
        result = ""
        for line in index:
            result += line
        return result


@app.route("/api/chat/<room>", methods=["POST", "GET"])
def post_chat(room):
    if not is_valid_room(room):
        return Response(status=404)

    if request.method == "POST":
        user_name = request.form['username']
        message = request.form['msg']
        time = datetime.now()
        formatted_time = f"[{time.year}-{time.month}-{time.day} {time.hour}:{time.minute}:{time.second}]"

        result = write_message_to_lobby(
            room, user_name, message, formatted_time)

        return result if result else Response(status=200)

    messages = read_lobby_messages(room)
    return messages if messages else ""


if __name__ == "__main__":
    app.run()
