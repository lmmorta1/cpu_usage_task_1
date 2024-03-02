from flask import Flask, render_template
import sqlite3

app = Flask(__name__)

def connect_db():
    conn = sqlite3.connect('cpu_usage.sqlite')
    return conn

@app.route('/')
def index():
    conn = connect_db()
    cursor = conn.cursor()
    cursor.execute("SELECT * FROM cpu_usage")
    data = cursor.fetchall()
    conn.close()

    return render_template('index.html', data=data)

if __name__ == '__main__':
    app.run(debug=True)
