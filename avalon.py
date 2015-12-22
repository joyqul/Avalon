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
    return redirect(url_for("login"))
    
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
counter = [i for i in xrange(100)];
assignCount = [[2, 3, 2, 3, 3], [2, 3, 4, 3, 4], [2, 3, 3, 4, 4], [3, 4, 4, 5, 5], [3, 4, 4, 5, 5], [3, 4, 4, 5, 5]]
successCount = [[2, 3, 2, 3, 3], [2, 3, 4, 3, 4], [2, 3, 3, 3, 4], [3, 4, 4, 4, 5], [3, 4, 4, 4, 5], [3, 4, 4, 4, 5]]
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
    for i in xrange(100):
        if i in counter:
            for room in rooms.keys():
                if room == i:
                    del rooms[i];
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
    if roomId<0 or roomId >=100 or roomId in counter:
        return redirect(url_for("roomList"))
    now = rooms[roomId];
    if now["count"] > 10:
        return redirect(url_for("roomList"))
    if session.get("userId") not in now["players"]:
        now["count"] = now["count"] + 1;
        now["players"].append(session.get("userId"))
    if now["state"] == "choose":
        return redirect(url_for("choose", roomId=roomId))
    if now["state"] == "vote":
        return redirect(url_for("vote", roomId=roomId))
    if now["state"] == "quest":
        return redirect(url_for("quest", roomId=roomId))   
    if now["state"] == "assassination":
        return redirect(url_for("assassination", roomId=roomId))
    if now["state"] == "result":
        return redirect(url_for("roundResult", roomId=roomId))
    if now["state"] == "over":
        return redirect(url_for("gameResult", roomId=roomId))
    now["chooseNumber"] = ['?','?','?','?','?']
    if request.method == "POST" and request.form["submit"] == "START":
        if now["count"] >= 5:
            now["state"] = "choose"
            now["questRound"] = 0
            now["voteRound"] = 0
            now["arthur"] = 0;
            now["playerId"] = []
            now["successRound"] = 0
            now["voteResult"] = {}
            now["questResult"] = []
            now["chooseRecord"] = {}
            now["chooseNumber"] = list(assignCount[now["count"]-5])
            global roles
            role = list(roles[now["count"]-5])
            random.shuffle(role)
            random.shuffle(now["players"])
            fieldList = ["result", "playerCount", "findMerlin"]
            valueList = ["00000", now["count"], False]
            now["minions"] = []
            showRole = []
            for i in xrange(now["count"]):
                voteId = insert("votes", ["vote00"], ["NULL"])
                assignId = insert("assign", ["assign00"], ["NULL"])
                questId = insert("quests", ["quest0"], ["NULL"])
                userId = g.db.execute("select id from users where username=?", [now["players"][i]]).fetchall()
                print "userID : ", userId
                playerId = insert("players", ["role", "userId", "voteId", "questId", "assignId", "ordering"], [role[i], userId[0][0], voteId, questId, assignId, i])
                now["playerId"].append(playerId)
                fieldList.append("player%d" % (i))
                valueList.append(playerId)
                if role[i] == "merlin":
                    now["merlin"] = now["players"][i]
                if role[i] == "percival":
                    now["percival"] = now["players"][i]
                if role[i] == "assassin":
                    now["assassin"] = now["players"][i]
                    now["minions"].append(now["players"][i])
                if role[i] == "morgana":
                    now["morgana"] = now["players"][i]
                    now["minions"].append(now["players"][i])
                if role[i] == "minion":
                    now["minions"].append(now["players"][i])
                
            for i in xrange(now["count"]):
                showRole.append([])
                for nowRole in role:
                    if role[i] == "servant":
                        showRole[i].append("Unknown")
                    if role[i] == "merlin":
                        if nowRole == "minion" or nowRole == "assassin" or nowRole == "morgana":
                            showRole[i].append("Minion of Mordred")
                        elif nowRole == "merlin":
                            showRole[i].append("Merlin : Servant of Arthur")
                        else:
                            showRole[i].append("Servant of Arthur")
                    if role[i] == "percival":
                        if nowRole == "percival":
                            showRole[i].append("Percival : Servant of Arthur")
                        elif nowRole == "merlin" or nowRole == "morgana":
                            showRole[i].append("Merlin or Morgana")
                        else:
                            showRole[i].append("Unknown")
                    if role[i] == "minion":
                        if nowRole == role[i]:
                            showRole[i].append("Minion of Mordred")
                        elif nowRole == "assassin" or nowRole == "morgana" or nowRole == "minion":
                            showRole[i].append("Minion of Mordred")
                        else:
                            showRole[i].append("Servant of Arthur")
                    if role[i] == "morgana":
                        if nowRole == role[i]:
                            showRole[i].append("Morgana : Minion of Mordred")
                        elif nowRole == "assassin" or nowRole == "morgana" or nowRole == "minion":
                            showRole[i].append("Minion of Mordred")
                        else:
                            showRole[i].append("Servant of Authur")
                    if role[i] == "assassin":
                        if nowRole == role[i]:
                            showRole[i].append("Assassin : Minion of Mordred")
                        elif nowRole == "assassin" or nowRole == "morgana" or nowRole == "minion":
                            showRole[i].append("Minion of Mordred")
                        else:
                            showRole[i].append("Servant of Arthur")
                if role[i] == "servant":
                    showRole[i][i] = "Servant of Arthur"
            
            fieldList.append("result")
            valueList.append("")
            gameId = insert("games", fieldList, valueList)
            now["gameId"] = gameId
            now["showRole"] = showRole
            return redirect(url_for("choose", roomId=roomId))
    elif request.method == "POST" and request.form["submit"] == "EXIT":
        now["count"] -= 1;
        now["players"].remove(session.get("userId"));
        if now["owner"] == session.get("userId"):
            if len(now["players"]) != 0:
                now["owner"] = now["players"][0];
            else:
                counter.append(now["id"]);
        return redirect(url_for("roomList"));
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
        print "assigment "+assignment
        myId = now["playerId"][now["arthur"]]
        assignId = g.db.execute("select assignId from players where id=?", [myId]).fetchall()[0][0]
        update("assign", "assign%02d"%index, "'%s'" % (assignment), "id=%d" % (assignId));
        now["state"] = "vote"
        now["voted"] = [];
        now["seenVote"] = [];
        now["agreed"] = [];
        now["assignment"] = {}
        index = 0
        for player in now["players"]:
            if assignment[index] == "0":
                now["assignment"][player] = False;
            else:
                now["assignment"][player] = True;
            index = index+1
        now["chooseRecord"][now["questRound"]*5+now["voteRound"]] = now["assignment"] 
        return redirect(url_for("vote", roomId=roomId));
    if isArthur:
        return render_template("choose.html", roomId=roomId, room=now, chooseNumber=chooseNumber)
    else:
        return render_template("wait_choose.html", roomId=roomId, room=now, chooseNumber=chooseNumber)
    
@app.route("/room/<int:roomId>/vote", methods=["POST", "GET"])
def vote(roomId):
    now = rooms[roomId];
    if now["state"] != "vote":
        return redirect(url_for("room", roomId=roomId))
    if session.get("userId") in now["voted"]:
        return redirect(url_for("waitVote", roomId=roomId))
    isArthur = session.get("userId")==now["players"][now["arthur"]]
    isChosen = now["assignment"]
    print isChosen
    if request.method == "POST":
        now["voted"].append(session.get("userId"));
        result = request.form["vote"];
        print "vote " + result;
        if result == "agree":
            now["agreed"].append(session.get("userId"));
        index = now["questRound"]*5 + now["voteRound"]
        myId = now["playerId"][now["players"].index(session.get("userId"))]
        voteId = g.db.execute("select voteId from players where id=?", [myId]).fetchall()[0][0]
        update("votes", "vote%02d"%index, "'%s'" % (result), "id=%d" % (voteId));
        return redirect(url_for("vote", roomId=roomId));
    return render_template("vote.html", roomId=roomId, room=now, isArthur=isArthur, isChosen=isChosen)
    
@app.route("/room/<int:roomId>/wait_vote")
def waitVote(roomId):
    now = rooms[roomId]
    if now["state"] != "vote":
        return redirect(url_for("room", roomId=roomId))
    if session.get("userId") not in now["voted"]:
        return redirect(url_for("vote", roomId=roomId))
    if len(now["seenVote"]) == now["count"]:
        index = now["questRound"]*5 + now["voteRound"];
        now["voteResult"][index] = now["agreed"]
        agreeCount = len(now["agreed"])
        if agreeCount+agreeCount > now["count"]:
            now["state"] = "quest"
            now["successCount"] = 0
            now["quested"] = []
            return redirect(url_for("quest", roomId=roomId))
        else:
            now["arthur"] = (now["arthur"] + 1) % now["count"]
            now["voteRound"] = now["voteRound"] + 1
            if now["voteRound"] == 5:
                now["winner"] = "Mordred"
                now["state"] = "over"
                return redirect(url_for("gameResult", roomId=roomId))
            now["state"] = "choose"
            return redirect(url_for("choose", roomId=roomId))
    if(session.get("userId") not in now["seenVote"]):
        now["seenVote"].append(session.get("userId"));
    return render_template("wait_vote.html", roomId=roomId, room=now, voted=now["voted"], agreed=now["agreed"], voteCount=len(now["voted"]))
    
@app.route("/room/<int:roomId>/quest", methods=["POST", "GET"])
def quest(roomId):
    now = rooms[roomId]
    isChosen = now["assignment"]
    if now["state"] != "quest":
        return redirect(url_for("room", roomId=roomId))
    if session.get("userId") in now["quested"]:
        return redirect(url_for("waitQuest", roomId=roomId))
    if not isChosen[session.get("userId")]:
        return redirect(url_for("waitQuest", roomId=roomId))
    if request.method == "POST" and isChosen[session.get("userId")]:
        result = request.form["quest"];
        print result;
        now["quested"].append(session.get("userId"));
        if result == "succeed":
            now["successCount"] = now["successCount"] + 1;
        myId = now["playerId"][now["players"].index(session.get("userId"))]
        questId = g.db.execute("select questId from players where id=?", [myId]).fetchall()[0][0]
        update("quests", "quest%01d"%now["questRound"], "'%s'" % (result), "id=%d" % (questId));
        return redirect(url_for("quest", roomId=roomId));
    return render_template("quest.html", roomId=roomId, room=now, isChosen=isChosen)
    
@app.route("/room/<int:roomId>/wait_quest")
def waitQuest(roomId):
    now = rooms[roomId]
    isChosen = now["assignment"]
    if now["state"] != "quest":
        return redirect(url_for("room", roomId=roomId))
    if len(now["quested"]) == assignCount[now["count"]-5][now["questRound"]]:
        now["state"] = "result"
        now["seeResult"] = []
        failCount = assignCount[now["count"]-5][now["questRound"]] - now["successCount"]; 
        if now["successCount"] >= successCount[now["count"]-5][now["questRound"]]:
            now["successRound"] = now["successRound"] + 1;
            now["questResult"].append(True);
        else:
            now["questResult"].append(False)
        now["lastResult"] = [now["successCount"], assignCount[now["count"]-5][now["questRound"]], successCount[now["count"]-5][now["questRound"]]]
        result = g.db.execute("select result from games where id=?", [now["gameId"]]).fetchall()[0][0]
        result = result + str(failCount)
        update("games", "result", "'%s'" % (result), "id=%d" % (now["gameId"]));
        if now["successRound"] == 3:
            now["state"] = "assassination"
            return redirect(url_for("assassination", roomId=roomId)) 
        if(now["questRound"]+1 - now["successRound"] == 3):
            now["winner"] = "Mordred"
            now["state"] = "over"
            now["done"] = [];
            now["nextRoom"] = -1;
            return redirect(url_for("gameResult", roomId=roomId))
        return redirect(url_for("roundResult", roomId=roomId))
            
    return render_template("wait_quest.html", roomId=roomId, room=now, voted=now["quested"], isChosen=isChosen)
  
@app.route("/room/<int:roomId>/round_result")
def roundResult(roomId):
    now = rooms[roomId]
    if now["state"] != "result":
        return redirect(url_for("room", roomId=roomId))
    if len(now["seeResult"]) == now["count"]:
        now["state"] = "choose"
        now["arthur"] = (now["arthur"] + 1) % now["count"]
        now["questRound"] = now["questRound"]+1
        now["voteRound"] = 0
    if session.get("userId") not in now["seeResult"]:
        now["seeResult"].append(session.get("userId"))
    return render_template("round_result.html", roomId=roomId, room=now)

@app.route("/room/<int:roomId>/assassination", methods = ["POST", "GET"])
def assassination(roomId):
    now = rooms[roomId]
    if now["state"] != "assassination":
        return redirect(url_for("room", roomId=roomId))
    isAssassin = session.get("userId") == now["assassin"]
    if request.method == "POST" and isAssassin:
        result = request.form["kill"]
        findMerlin = False
        now["winner"] = "Arthur"
        if result == now["merlin"]:
            findMerlin = True
            now["winner"] = "Mordred"
        update("games", "findMerlin", findMerlin, "id=%d" % (now["gameId"]));
        now["state"] = "over"
        now["done"] = [];
        now["nextRoom"] = -1;
        return redirect(url_for("gameResult", roomId=roomId))
    return render_template("assassination.html", roomId=roomId, room=now, isAssassin=isAssassin)
    
@app.route("/room/<int:roomId>/game_result", methods = ["POST", "GET"])
def gameResult(roomId):
    now = rooms[roomId]
    if now["state"] != "over":
        return redirect(url_for("room", roomId=roomId))
    result = ""
    if now["winner"] == "Arthur":
        result = "The loyal servants of King Arthur achieved victory!"
        myId = now["playerId"][now["players"].index(session.get("userId"))]
        userId = g.db.execute("select userId from players where id=?", [myId]).fetchall()[0][0]
        if session.get("userId") in now["minions"]:
            update("users", "lose", "lose + 1", "id=%d" % (userId));
        else:
            update("users", "win", "win + 1", "id=%d" % (userId));
        
    else:
        result = "The evil minions of Mordred destroyed the rule of justice!"
        myId = now["playerId"][now["players"].index(session.get("userId"))]
        userId = g.db.execute("select userId from players where id=?", [myId]).fetchall()[0][0]
        if session.get("userId") in now["minions"]:
            update("users", "win", "win + 1", "id=%d" % (userId));
        else:
            update("users", "lose", "lose + 1", "id=%d" % (userId));
    if request.method == "POST":
        if session.get("userId") not in now["done"]:
            now["done"].append(session.get("userId"))
        if len(now["done"]) == now["count"]:
            counter.append(now["id"]);
        if now["nextRoom"] == -1 :
            thisId = counter.pop(0);
            now["nextRoom"] = thisId;
            newItem = {"name":now["name"], "id":thisId, "owner":session.get("userId"), "count":0, "players":[], "state":"prepare"}
            rooms[thisId] = newItem
            return redirect(url_for("room", roomId=newItem["id"]));
        else:
            return redirect(url_for("room", roomId=now["nextRoom"]));
        
    return render_template("game_result.html", roomId=roomId, room=now, result=result)
    
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
            thisId = counter.pop(0)
            newItem = {"name":request.form["roomname"], "id":thisId, "owner":session.get("userId"), "count":0, "players":[], "state":"prepare"}
            rooms[thisId] = newItem
            return redirect(url_for("room", roomId=thisId));
    return render_template("createroom.html")
    
if __name__ == "__main__":
    app.run()
