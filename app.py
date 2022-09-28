import os

from cs50 import SQL
from flask import Flask, flash, redirect, render_template, request, session
from flask_session import Session
from werkzeug.security import check_password_hash, generate_password_hash
from helpers import apology, login_required
import werkzeug
from datetime import datetime

app = Flask(__name__, static_folder='upload')

app.config["TEMPLATES_AUTO_RELOAD"] = True

app.config["SESSION_PERMANENT"] = False
app.config["SESSION_TYPE"] = "filesystem"
Session(app)

db = SQL("sqlite:///ohitori.db")

# 画像のアップロード
UPLOAD_POST_FOLDER = './upload'
ALLOWED_EXTENSIONS = set(['.jpg','.gif','.png','image/gif','image/jpeg','image/png'])
app.config['UPLOAD_FOLDER'] = UPLOAD_POST_FOLDER
count = 0


@app.after_request
def after_request(response):
    """Ensure responses aren't cached"""
    response.headers["Cache-Control"] = "no-cache, no-store, must-revalidate"
    response.headers["Expires"] = 0
    response.headers["Pragma"] = "no-cache"
    return response


@app.route("/")
@login_required
def index():
    return redirect("/home")

@app.route("/login", methods=["GET", "POST"])
def login():
    """Log user in"""
    session.clear()

    if request.method == "POST":

        if not request.form.get("username"):
            return apology("must provide username", 403)

        elif not request.form.get("password"):
            return apology("must provide password", 403)

        username = request.form.get("username")
        rows = db.execute("SELECT * FROM users WHERE username = ?", username)

        if len(rows) != 1 or not check_password_hash(rows[0]["hash"], request.form.get("password")):
            return apology("invalid username and/or password", 403)

        session["user_id"] = rows[0]["id"]

        if db.execute("SELECT userid FROM users WHERE username = ?",username)[0]["userid"] == 0:
            db.execute("UPDATE users SET userid=(?) WHERE username=(?)",session["user_id"],username)

        return redirect("/mypage")

    else:
        return render_template("login.html")


@app.route("/post", methods=["GET", "POST"])
def post():
    if request.method == "POST":
        userid = session["user_id"]
        goon = request.form.get("goon")
        if len(goon) < 4:
            goon=None
        text = request.form.get("text")
        filepath=None
        img = request.files['imgfile']
        if img:
            filepath = datetime.now().strftime("%Y%m%d_%H%M%S_") \
            + werkzeug.utils.secure_filename(img.filename)
            img.save(os.path.join(app.config['UPLOAD_FOLDER'] + '/postimg', filepath))

        db.execute("INSERT INTO posts (userid,go_on,post_text,photo_path) VALUES(?,?,?,?)",userid,goon,text,filepath)
        return redirect("/")
    else:
        return render_template("post.html")

@app.errorhandler(werkzeug.exceptions.RequestEntityTooLarge)
def handle_over_max_file_size(error):
    print("werkzeug.exceptions.RequestEntityTooLarge")
    return 'result : file size is overed.'

@app.route("/home")
def home():
    posts = db.execute("SELECT go_on,post_text,photo_path,posted_at,like,users.display_name AS display_name,users.icon AS icon FROM posts JOIN users ON posts.userid = users.userid ORDER BY posted_at DESC")
    return render_template("home.html",posts=posts)


@app.route("/mypage", methods=["GET", "POST"])
def mypage():
    if request.method == "POST":
        return redirect("/")
    else:
        userid = session["user_id"]
        users = db.execute("SELECT display_name,icon,comment,created_at,follow,follower FROM users WHERE userid = (?)", userid)
        posts = db.execute("SELECT go_on,post_text,photo_path,posted_at,like FROM posts WHERE userid = (?) ORDER BY posted_at DESC", userid)
        return render_template("mypage.html",posts=posts,users=users)


@app.route("/set", methods=["GET", "POST"])
def set():
    if request.method == "POST":
        userid = session["user_id"]
        nickname = request.form.get("nickname")
        comment = request.form.get("comment")
        if db.execute("SELECT icon FROM users WHERE userid = ?",userid)[0]["icon"] == None:
            filepath=None
        else:
            filepath=db.execute("SELECT icon FROM users WHERE userid = ?",userid)[0]["icon"]

        img = request.files['imgfile']
        if img:
            filepath = datetime.now().strftime("%Y%m%d_%H%M%S_") \
            + werkzeug.utils.secure_filename(img.filename)
            img.save(os.path.join(app.config['UPLOAD_FOLDER'] + '/iconimg', filepath))

        db.execute("UPDATE users SET display_name=(?), icon=(?), comment=(?) WHERE userid=(?)",nickname,filepath,comment,userid)
        return redirect("/mypage")
    else:
        userid = session["user_id"]
        users = db.execute("SELECT display_name,icon,comment FROM users WHERE userid = (?)", userid)
        return render_template("set.html",users=users)


@app.route("/register", methods=["GET", "POST"])
def register():
    """Register user"""
    if request.method == "POST":
        # 入力を受け取る
        username = request.form.get("username")
        password = request.form.get("password")
        confirmation = request.form.get("confirmation")
        # ユーザ名の被りを確かめる
        users = int(db.execute("SELECT COUNT(username) as username FROM users where username=(?)", username)[0]["username"])
        # 名前のカウントが1以上、パスワードが再入力と異なる、入力されていないものがある場合
        if users >= 1 or password != confirmation or not username or not password or not confirmation:
            return apology("COULDN'T REGISTER", 400)
        # パスワードをハッシュ化する
        password = generate_password_hash(password)
        # usersにそれぞれのデータを入れる
        db.execute("INSERT INTO users (username,hash) VALUES(?,?)", username,password)
        return redirect("/login")
    else:
        return render_template("register.html")


@app.route("/logout")
def logout():
    """Log user out"""

    # sessionを削除する
    session.clear()

    # ログインフォームに移動する
    return redirect("/")

