import sqlite3
from flask import Flask, redirect, url_for, flash, render_template, request

app = Flask(__name__)
app.config.from_pyfile("config.txt")

def connectDatabase():
    return sqlite3.connect(app.config["DATABASE"]);
    
@app.route("/")
def root():
    return render_template("index.html")
#return redirect(url_for("login"))
    
@app.route("/login", methods=["GET", "POST"])
def login():
    error=None
    if request.method == "POST":
        print request.form["username"] , request.form["password"]
        if request.form["username"] != "admin" or request.form["password"] != "secret":
            error = "Wrong password!"
        else:
            flash("Log in successful!")
            return redirect(url_for("root"));
    return render_template("login.html", error=error)
#    return "This is log-in page"
 
@app.route("/signup")
def signUp():
    return "This is sign-up page"
    
@app.route("/room")
def roomList():
    return "This is room list"
    
@app.route("/room/<int:roomID>")
def room(roomID):
    return "This is room ID %d." % roomID
    
@app.route("/room/create")
def createRoom():
    return "This is create room"
    
#@app.route("")
    
if __name__ == "__main__":
    app.run(host="0.0.0.0")
