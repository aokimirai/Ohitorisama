import os
from flask import Flask, flash, redirect, render_template, request, session
from flask_session.__init__ import Session
from werkzeug.security import check_password_hash, generate_password_hash
from helpers import apology, login_required
import werkzeug
from datetime import datetime
import sqlite3

app = Flask(__name__, static_folder='upload')

app.config["TEMPLATES_AUTO_RELOAD"] = True


# Configure session to use filesystem (instead of signed cookies)
# ファイルシステムを使用するようにセッションを構成します (署名付き Cookie の代わりに)
app.config["SESSION_PERMANENT"] = False
app.config["SESSION_TYPE"] = "filesystem"
Session(app)

# 画像のアップロード
UPLOAD_POST_FOLDER = './upload'
ALLOWED_EXTENSIONS = set(['.jpg','.gif','.png','image/gif','image/jpeg','image/png'])
app.config['UPLOAD_FOLDER'] = UPLOAD_POST_FOLDER

def db(ope):
    con = sqlite3.connect('./ohitori.db')
    db = con.cursor()
    db = db.execute(ope)
    con.close()
    return db


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
    #　ユーザーidをクリアする
    session.clear()
    username = request.form.get("username")
    password = request.form.get("password")
    # POSTの場合
    if request.method == "POST":
        # ユーザーネームが入力されていない
        if not username:
            return apology("ユーザーネームを入力してください", 403)
        # パスワードが入力されていない
        elif not password:
            return apology("パスワードを入力してください", 403)

        con = sqlite3.connect('./ohitori.db')
        db = con.cursor()
        db.execute("SELECT * FROM users WHERE username = ?", (username,))
        users = db.fetchone()
        con.close()
        # ユーザーネームとパスワードが正しいか確認
        if users != None:
            if check_password_hash(users[2], password):
                # ユーザーを記憶する
                session["user_id"] = users[0]
                #メッセージ
                flash("ログインしました")
                return redirect("/mypage")
            else:
                return apology("パスワードが無効です", 403)
        else:
            return apology("ユーザネームが無効です", 403)

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
        con = sqlite3.connect("./ohitori.db")
        db = con.cursor()
        db.execute("INSERT INTO posts (userid,go_on,post_text,photo_path) VALUES(?,?,?,?)",(userid,goon,text,filepath,))
        con.commit()
        con.close()
        return redirect("/")
    else:
        return render_template("post.html")

@app.errorhandler(werkzeug.exceptions.RequestEntityTooLarge)
def handle_over_max_file_size(error):
    print("werkzeug.exceptions.RequestEntityTooLarge")
    return 'result : file size is overed.'

@app.route("/home")
def home():
    con = sqlite3.connect("./ohitori.db")
    db = con.cursor()
    posts = db.execute("SELECT go_on,post_text,photo_path,posted_at,like,users.display_name AS display_name,users.icon AS icon FROM posts JOIN users ON posts.userid = users.id ORDER BY posted_at DESC").fetchall()
    con.close()
    print(posts)
    return render_template("home.html",posts=posts)


@app.route("/mypage", methods=["GET", "POST"])
def mypage():
    if request.method == "POST":
        return redirect("/")
    else:
        userid = session["user_id"]
        con = sqlite3.connect('./ohitori.db')
        db = con.cursor()
        users = db.execute("SELECT display_name,icon,comment,created_at FROM users WHERE id = ?", (userid,)).fetchall()
        posts = db.execute("SELECT go_on,post_text,photo_path,posted_at,like FROM posts WHERE userid = ? ORDER BY posted_at DESC", (userid,)).fetchall()
        con.close()
        return render_template("mypage.html",posts=posts,users=users)


@app.route("/set", methods=["GET", "POST"])
def set():
    if request.method == "POST":
        userid = session["user_id"]
        nickname = request.form.get("nickname")
        comment = request.form.get("comment")
        con = sqlite3.connect("./ohitori.db")
        db = con.cursor()
        users = db.execute("SELECT icon FROM users WHERE id = ?",(userid,)).fetchone()
        if users[0] == None:
            filepath=None
        else:
            filepath=db.execute("SELECT icon FROM users WHERE id = ?",userid)[0]["icon"]

        img = request.files['imgfile']
        if img:
            filepath = datetime.now().strftime("%Y%m%d_%H%M%S_") \
            + werkzeug.utils.secure_filename(img.filename)
            img.save(os.path.join(app.config['UPLOAD_FOLDER'] + '/iconimg', filepath))
        
        db.execute("UPDATE users SET display_name=?, icon=?, comment=? WHERE id=?",(nickname,filepath,comment,userid,))
        con.commit()
        con.close()
        return redirect("/mypage")
    else:
        userid = session["user_id"]
        con = sqlite3.connect("./ohitori.db")
        db = con.cursor()
        users = db.execute("SELECT display_name,icon,comment FROM users WHERE id = (?)", (userid,)).fetchall()
        return render_template("set.html",users=users)


@app.route("/register", methods=["GET", "POST"])
def register():
    if request.method == "POST":
        # ユーザーネームが入力されていない
        username = request.form.get("username")
        password = request.form.get("password")
        if not username:
            return apology("ユーザーネームを入力してください", 400)
        # ユーザーネームが既に使われている
        con = sqlite3.connect('./ohitori.db')
        db = con.cursor()
        db.execute("SELECT * FROM users where username=?", (username,))
        user = db.fetchone()
        if user != None:
            return apology("このユーザーネームは既に使われています", 400)
        # パスワードが入力されていない
        elif not password:
            return apology("パスワードを入力してください", 400)
        # パスワードが一致しない
        elif password != request.form.get("confirmation"):
            return apology("パスワードが一致しません", 400)
        con.close()
        password = generate_password_hash(password)
        # データベースに入れる
        con = sqlite3.connect('./ohitori.db')
        db = con.cursor()
        db.execute("INSERT INTO users (username, hash) VALUES(?, ?)", (username, password))
        con.commit()
        con.close()
        #メッセージ
        flash("登録が完了しました")
        # ログインページに送る
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

