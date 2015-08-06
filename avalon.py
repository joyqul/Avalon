import sqlite3
import hashlib
import random
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
assignCount = [[2, 3, 2, 3, 3], [2, 3, 4, 3, 4], [2, 3, 3, 4, 4], [3, 4, 4, 5, 5], [3, 4, 4, 5, 5], [3, 4, 4, 5, 5]]   
roles = [["merlin", "assassin", "servant", "servant", "minion"],\
      ["merlin", "assassin", "servant", "servant", "minion", "servant"],\
      ["merlin", "assassin", "servant", "servant", "minion", "morgana", "percival"],\
      ["merlin", "assassin", "servant", "servant", "minion", "morgana", "percival", "servant"],\
      ["merlin", "assassin", "servant", "servant", "minion", "morgana", "percival", "servant", "servant"],\
      ["merlin", "assassin", "servant", "servant", "minion", "morgana", "percival", "servant", "servant", "minion"]]

@app.route("/room")
def roomList():
    if not session.get("loggedIn"):
        abort(401)
    global rooms;
    result = g.db.execute("select win, lose from users where username=?", [session.get("userId")]).fetchall()
    print result
    win, lose = result[0]
    return render_template("roomlist.html", rooms=rooms, userId=session.get("userId"), win=win, lose=lose)

def insert(table, fields=[], values=[]):
    cur = g.db.cursor()
    query = "INSERT INTO %s (%s) VALUES (%s)" % (table, ", ".join(fields), ", ".join(["?"]*len(values)))
    print "execute SQL : \""+query+"\""
    cur.execute(query, values)
    g.db.commit()
    id = cur.lastrowid
    cur.close()
    return id;
    
def update(table, field, value, condition):
    cur = g.db.cursor()
    query = "UPDATE %s SET %s = ? WHERE %s " % (table, field, condition)
    print "execute SQL : \""+query+"\""
    cur.execute(query, [value])
    g.db.commit()
    cur.close()
    
@app.route("/room/<int:roomId>", methods = ["GET", "POST"])
def room(roomId):
    if not session.get("loggedIn"):
        abort(401)
    print "Enter room %d, now state %s" % (roomId, rooms[roomId]["state"])
    if roomId not in rooms:
        return redirect(url_for("roomList"))
    now = rooms[roomId];
    if now["count"] > 10:
        return redirect(url_for("roomList"))
    if(session.get("userId") not in now["players"]):
        now["count"] = now["count"] + 1;
        now["players"].append(session.get("userId"))
    if(now["state"] == "choose"):
        print "redirect to choose"
        return redirect(url_for("choose", roomId=roomId))
    if(now["state"] == "vote"):
        return redirect(url_for("vote", roomId=roomId))
    if(now["state"] == "quest"):
        return redirect(url_for("quest", roomId=roomId))   
    if request.method == "POST":
        if now["count"] >= 5:
            now["state"] = "choose"
            now["questRound"] = 0
            now["voteRound"] = 0
            now["arthur"] = 0;
            now["playerId"] = []
            global roles
            role = list(roles[now["count"]-5])
            random.shuffle(role)
            random.shuffle(now["players"])
            fieldList = ["result", "playerCount", "findMerlin"]
            valueList = ["00000", now["count"], False]
            for i in xrange(now["count"]):
                voteId = insert("votes", ["vote00"], ["NULL"])
                assignId = insert("assign", ["assign00"], ["NULL"])
                questId = insert("quests", ["quest0"], ["NULL"])
                userId = g.db.execute("select id from users where username=?", [session.get("userId")]).fetchall()
                print "userID : ", userId
                playerId = insert("players", ["role", "userId", "voteId", "questId", "assignId", "ordering"], [role[i], userId[0][0], voteId, questId, assignId, i])
                now["playerId"].append(playerId)
                fieldList.append("player%d" % (i))
                valueList.append(playerId)
            
            gameId = insert("games", fieldList, valueList)
            now["gameId"] = gameId
            return redirect(url_for("choose", roomId=roomId))
    return render_template("room.html", room=now, roomId=roomId, isOwner=(session.get("userId")==now["owner"]));


@app.route("/room/<int:roomId>/choose", methods=["POST", "GET"])
def choose(roomId):
    now = rooms[roomId]
    if(now["state"] != "choose"):
        return redirect(url_for("room", roomId=roomId));
    isArthur = session.get("userId")==now["players"][now["arthur"]];
    chooseNumber = assignCount[now["count"]-5][now["questRound"]];
    if request.method == "POST":
        result = request.form.getlist("proposal");
        index = now["questRound"] * 5 + now["voteRound"];
        assignment = "";
        for player in now["players"]:
            if player in result:
                assignment += "1"
            else: 
                assignment += "0"
        print assignment
        myId = now["playerId"][now["arthur"]]
        voteId = g.db.execute("select voteId from players where id=?", [myId]).fetchall()[0][0]
        update("assign", "assign%02d"%index,"'%s'" % (assignment), "id=%d" % (voteId));
        now["state"] = "vote"
        now["assignment"] = assignment
        return redirect(url_for("vote", roomId=roomId));
    return render_template("choose.html", roomId=roomId, room=now, isArthur=isArthur, chooseNumber=chooseNumber)
    
@app.route("/room/<int:roomId>/vote")
def vote(roomId):
    return render_template("room.html", roomId=roomId)
    
@app.route("/room/<int:roomId>/quest")
def quest(roomId):
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
            newItem = {"name":request.form["roomname"], "id":counter, "owner":session.get("userId"), "count":0, "players":[], "state":"prepare"}
            rooms[counter] = newItem
            counter += 1
            return redirect(url_for("room", roomId=newItem["id"]));
    return render_template("createroom.html")
    
if __name__ == "__main__":
    app.run(host="0.0.0.0")
