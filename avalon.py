import sqlite3
import hashlib
from flask import Flask, redirect, url_for, flash, render_template, request, g

app = Flask(__name__)
app.config.from_pyfile("config.txt")

def connectDatabase():
    return sqlite3.connect(app.config["DATABASE"]);
 
@app.before_request
def before_request():
    g.db = connectDatabase()

@app.teardown_request
def teardown_request(exception):
    db = getattr(g, "db", None)
    if db is not None:
        db.close()
    
@app.route("/")
def root():
    return render_template("index.html")
#return redirect(url_for("login"))
    
@app.route("/login", methods=["GET", "POST"])
def login():
    error=None
    if request.method == "POST":
        print "login request form : ", request.form["username"] , request.form["password"]
        result = g.db.execute("select password from users where username=? and password=?", [request.form['username'], hashlib.md5(request.form["password"]).hexdigest()]).fetchall();
        print "result : ", result
        if len(result) == 0:
            error = "Username or password incorrect!"
        else:
            flash("Log in successful!")
            return redirect(url_for("roomList"));
    return render_template("login.html", error=error)
#    return "This is log-in page"
 
@app.route("/signup", methods=["GET", "POST"])
def signUp():
    error = None
    if request.method == "POST":
        print "signup request form : ", request.form["username"],\
        request.form["password"], request.form["retypePassword"]
        result = g.db.execute("select password from users where username=?", [request.form['username']]).fetchall();
        if request.form["password"] != request.form["retypePassword"]:
            error = "Password mismatched!"
        elif len(result) != 0:
            error = "Username already exists."
        else:
            g.db.execute("insert into users (username, password, win, lose) values (?, ?, 0, 0)",\
                    [request.form["username"], hashlib.md5(request.form["password"]).hexdigest()])
            result = g.db.execute("select * from users where username=?", [request.form['username']]).fetchall();
            print "after execution : ", result
            g.db.commit()
            flash("Sign up successful!")
            return redirect(url_for("login"));
    return render_template("signup.html", error=error)
#    return "This is sign-up page"
    
@app.route("/room")
def roomList():
    return render_template("roomlist.html")
#    return "This is room list"
    
@app.route("/room/<int:roomID>")
def room(roomID):
    return render_template("room.html", roomID=roomID)
#    return "This is room ID %d." % roomID
    
@app.route("/room/create")
def createRoom():
    return render_template("createroom.html")
#    return "This is create room"
    
#@app.route("")
    
if __name__ == "__main__":
    app.run(host="0.0.0.0")
