from flask import Flask, jsonify
from flask import g
from db_utils import connect_to_db 

app = Flask(__name__)

@app.route("/")
def home():
    return "<h1>Hello, World!</h1><p>My new Flask app is running.</p>"

@app.before_request
def get_db():
    if 'mysql_db' not in g:
        g.mysql_db = connect_to_db()

@app.teardown_request
def teardown_db(exception):
    db = g.pop('mysql_db', None)
    if db is not None:
        db.close() 

@app.route("/user/<user_id>")
def profile(user_id):
    cursor = g.mysql_db.cursor(dictionary=True)
    cursor.execute(f"SELECT id, username, created_at FROM users WHERE id = {user_id};")
    users = cursor.fetchone()
    cursor.close()
    return jsonify(users)

if __name__ == "__main__":
    app.run(debug=True)
