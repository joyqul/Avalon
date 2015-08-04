import sqlite3
import hashlib
from flask import Flask, redirect, url_for, flash, render_template, request, g, abort, session

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
    
@app.route("/login", methods=["GET", "POST"])
def login():
    error=None
    if request.method == "POST":
        print "login request form : ", request.form["username"] , request.form["password"]
        result = g.db.execute("select id from users where username=? and password=?", [request.form['username'], hashlib.md5(request.form["password"]).hexdigest()]).fetchall();
        print "result : ", result
        if len(result) == 0:
            error = "Username or password incorrect!"
        else:
            session["loggedIn"] = True
            session["userId"] = request.form["username"]
            flash("Log in successful!")
            print "User %d logged in" % result[0];
            return redirect(url_for("roomList"));
    return render_template("login.html", error=error)

@app.route("/logout")
def logout():
    if not session.get("loggedIn"):
        abort(401)
    session.pop("loggedIn", None)
    flash("You are logged out!")
    return redirect(url_for("root"))    
 
@app.route("/signup", methods=["GET", "POST"])
def signUp():
    error = None
    if request.method == "POST":
        print "signup request form : ", request.form["username"],\
        request.form["password"], request.form["retypePassword"]
        result = g.db.execute("select password from users where username=?", [request.form['username']]).fetchall()
        if request.form["password"] != request.form["retypePassword"]:
            error = "Password mismatched!"
        elif len(result) != 0:
            error = "Username already exists."
        else:
            g.db.execute("insert into users (username, password, win, lose) values (?, ?, 0, 0)",\
                    [request.form["username"], hashlib.md5(request.form["password"]).hexdigest()])
            result = g.db.execute("select * from users where username=?", [request.form['username']]).fetchall()
            print "after execution : ", result
            g.db.commit()
            flash("Sign up successful!")
            return redirect(url_for("login"))
    return render_template("signup.html", error=error)
    
rooms = {}
counter = 0
    
@app.route("/room")
def roomList():
    if not session.get("loggedIn"):
        abort(401)
    global rooms;
    result = g.db.execute("select win, lose from users where username=?", [session.get("userId")]).fetchall()
    print result
    win, lose = result[0]
    return render_template("roomlist.html", rooms=rooms, userId=session.get("userId"), win=win, lose=lose)

@app.route("/room/<int:roomId>")
def room(roomId):
    if not session.get("loggedIn"):
        abort(401)
    print "Enter room %d" % roomId
    if roomId not in rooms:
        return redirect(url_for("roomList"))
    now = rooms[roomId];
    if now["count"] > 10:
        return redirect(url_for("roomList"))
    if(session.get("userId") not in now["players"]):
        now["count"] = now["count"] + 1;
        now["players"].append(session.get("userId"))
                
            
    return render_template("room.html", roomId=roomId)
    
@app.route("/room/create", methods = ["GET", "POST"])
def createRoom():
    error = None
    if not session.get("loggedIn"):
        abort(401)
    if request.method == "POST":
        print "roomname : ", request.form["roomname"]
        nameLen = len(request.form["roomname"])
        if(nameLen<2 or nameLen>18):
            error = "Inappropriate length for your room name."
        else:
            global counter
            newItem = {"name":request.form["roomname"], "id":counter, "owner":session.get("userId"), "count":0, "players":[]}
            rooms[counter] = newItem
            counter += 1
            return redirect(url_for("room", roomId=newItem["id"]));
    return render_template("createroom.html")
    
if __name__ == "__main__":
    app.run(host="0.0.0.0")
