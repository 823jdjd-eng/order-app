from datetime import datetime
import json
import os
import sqlite3
import urllib.error
import urllib.request
from functools import wraps

from flask import Flask, jsonify, redirect, render_template, request, session, url_for
from werkzeug.security import check_password_hash, generate_password_hash


app = Flask(__name__)
app.secret_key = os.environ.get("SECRET_KEY", "dev-secret-key-change-me")
DB_PATH = os.path.join(app.root_path, "order_app.db")


MENU = [
    {
        "id": 1,
        "name": "招牌牛肉面",
        "category": "主食",
        "price": 28,
        "tag": "热卖",
        "sales": 386,
        "description": "慢炖牛腱、手工宽面、浓郁红汤",
        "image": "https://images.unsplash.com/photo-1555126634-323283e090fa?auto=format&fit=crop&w=640&q=80",
    },
    {
        "id": 2,
        "name": "黑椒鸡排饭",
        "category": "主食",
        "price": 32,
        "tag": "推荐",
        "sales": 291,
        "description": "现煎鸡排配黑椒汁，米饭软糯",
        "image": "https://images.unsplash.com/photo-1603133872878-684f208fb84b?auto=format&fit=crop&w=640&q=80",
    },
    {
        "id": 3,
        "name": "番茄炒蛋饭",
        "category": "主食",
        "price": 22,
        "tag": "经典",
        "sales": 214,
        "description": "酸甜番茄、滑嫩鸡蛋，家常口味",
        "image": "https://images.unsplash.com/photo-1512058564366-18510be2db19?auto=format&fit=crop&w=640&q=80",
    },
    {
        "id": 4,
        "name": "蒜蓉生菜",
        "category": "小菜",
        "price": 16,
        "tag": "清爽",
        "sales": 128,
        "description": "大火快炒，蒜香清脆",
        "image": "https://images.unsplash.com/photo-1546069901-ba9599a7e63c?auto=format&fit=crop&w=640&q=80",
    },
    {
        "id": 5,
        "name": "香辣鸡翅",
        "category": "小菜",
        "price": 24,
        "tag": "微辣",
        "sales": 176,
        "description": "外皮焦香，辣度温和",
        "image": "https://images.unsplash.com/photo-1567620832903-9fc6debc209f?auto=format&fit=crop&w=640&q=80",
    },
    {
        "id": 6,
        "name": "柠檬红茶",
        "category": "饮品",
        "price": 12,
        "tag": "冰饮",
        "sales": 242,
        "description": "鲜切柠檬，茶香清亮",
        "image": "https://images.unsplash.com/photo-1556679343-c7306c1976bc?auto=format&fit=crop&w=640&q=80",
    },
    {
        "id": 7,
        "name": "鲜榨橙汁",
        "category": "饮品",
        "price": 16,
        "tag": "鲜榨",
        "sales": 119,
        "description": "现榨橙汁，无额外加糖",
        "image": "https://images.unsplash.com/photo-1621506289937-a8e4df240d0b?auto=format&fit=crop&w=640&q=80",
    },
]

CATEGORY_ORDER = ["主食", "小菜", "饮品"]
orders = []


def get_db():
    conn = sqlite3.connect(DB_PATH)
    conn.row_factory = sqlite3.Row
    return conn


def init_db():
    with get_db() as conn:
        conn.execute(
            """
            CREATE TABLE IF NOT EXISTS users (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                username TEXT NOT NULL UNIQUE,
                password_hash TEXT NOT NULL,
                role TEXT NOT NULL DEFAULT 'customer',
                created_at TEXT NOT NULL
            )
            """
        )
        admin = conn.execute("SELECT id FROM users WHERE username = ?", ("admin",)).fetchone()
        if admin is None:
            conn.execute(
                "INSERT INTO users (username, password_hash, role, created_at) VALUES (?, ?, ?, ?)",
                (
                    "admin",
                    generate_password_hash("admin123"),
                    "admin",
                    datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
                ),
            )


def current_user():
    user_id = session.get("user_id")
    if not user_id:
        return None
    with get_db() as conn:
        return conn.execute(
            "SELECT id, username, role FROM users WHERE id = ?",
            (user_id,),
        ).fetchone()


def public_user(user):
    if user is None:
        return None
    return {"id": user["id"], "username": user["username"], "role": user["role"]}


def register_customer(username, password, confirm_password):
    if len(username) < 3:
        return None, "用户名至少 3 个字符"
    if len(password) < 6:
        return None, "密码至少 6 位"
    if password != confirm_password:
        return None, "两次输入的密码不一致"

    try:
        with get_db() as conn:
            cursor = conn.execute(
                "INSERT INTO users (username, password_hash, role, created_at) VALUES (?, ?, ?, ?)",
                (
                    username,
                    generate_password_hash(password),
                    "customer",
                    datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
                ),
            )
            return {
                "id": cursor.lastrowid,
                "username": username,
                "role": "customer",
            }, ""
    except sqlite3.IntegrityError:
        return None, "这个用户名已经被注册"


def authenticate(username, password):
    with get_db() as conn:
        user = conn.execute(
            "SELECT id, username, password_hash, role FROM users WHERE username = ?",
            (username,),
        ).fetchone()

    if user is None or not check_password_hash(user["password_hash"], password):
        return None
    return user


def remember_user(user):
    session["user_id"] = user["id"]
    session["username"] = user["username"]
    session["role"] = user["role"]


def login_required(view):
    @wraps(view)
    def wrapped(*args, **kwargs):
        if current_user() is None:
            if request.path.startswith("/api/"):
                return jsonify({"message": "请先登录"}), 401
            return redirect(url_for("login", next=request.path))
        return view(*args, **kwargs)

    return wrapped


def admin_required(view):
    @wraps(view)
    def wrapped(*args, **kwargs):
        user = current_user()
        if user is None:
            if request.path.startswith("/api/"):
                return jsonify({"message": "请先登录商家账号"}), 401
            return redirect(url_for("login", next=request.path))
        if user["role"] != "admin":
            if request.path.startswith("/api/"):
                return jsonify({"message": "没有商家权限"}), 403
            return redirect(url_for("index"))
        return view(*args, **kwargs)

    return wrapped


@app.get("/")
def index():
    categories = [category for category in CATEGORY_ORDER if any(d["category"] == category for d in MENU)]
    return render_template("index.html", menu=MENU, categories=categories, user=current_user())


@app.get("/admin")
def admin():
    user = current_user()
    return render_template(
        "admin.html",
        user=user,
        can_manage=bool(user and user["role"] == "admin"),
    )


@app.route("/register", methods=["GET", "POST"])
def register():
    error = ""
    if request.method == "POST":
        username = request.form.get("username", "").strip()
        password = request.form.get("password", "")
        confirm_password = request.form.get("confirm_password", "")

        user, error = register_customer(username, password, confirm_password)
        if user:
            remember_user(user)
            return redirect(url_for("index"))

    return render_template("auth.html", mode="register", error=error)


@app.route("/login", methods=["GET", "POST"])
def login():
    error = ""
    next_url = request.args.get("next") or request.form.get("next") or url_for("index")

    if request.method == "POST":
        username = request.form.get("username", "").strip()
        password = request.form.get("password", "")
        user = authenticate(username, password)

        if user is None:
            error = "用户名或密码错误"
        else:
            remember_user(user)
            return redirect(next_url)

    return render_template("auth.html", mode="login", error=error, next_url=next_url)


@app.get("/logout")
def logout():
    session.clear()
    return redirect(url_for("index"))


@app.get("/api/auth/me")
def auth_me():
    return jsonify({"user": public_user(current_user())})


@app.post("/api/auth/register")
def api_register():
    data = request.get_json(silent=True) or {}
    user, error = register_customer(
        data.get("username", "").strip(),
        data.get("password", ""),
        data.get("confirm_password", ""),
    )
    if error:
        return jsonify({"message": error}), 400
    remember_user(user)
    return jsonify({"user": user}), 201


@app.post("/api/auth/login")
def api_login():
    data = request.get_json(silent=True) or {}
    user = authenticate(data.get("username", "").strip(), data.get("password", ""))
    if user is None:
        return jsonify({"message": "用户名或密码错误"}), 400
    remember_user(user)
    return jsonify({"user": public_user(user)})


@app.post("/api/auth/logout")
def api_logout():
    session.clear()
    return jsonify({"message": "已退出登录"})


@app.post("/api/orders")
@login_required
def create_order():
    data = request.get_json(silent=True) or {}
    items = data.get("items", [])

    order_items = []
    total = 0
    menu_by_id = {dish["id"]: dish for dish in MENU}

    for item in items:
        dish = menu_by_id.get(item.get("id"))
        quantity = int(item.get("quantity", 0))
        if dish is None or quantity <= 0:
            continue

        subtotal = dish["price"] * quantity
        total += subtotal
        order_items.append(
            {
                "id": dish["id"],
                "name": dish["name"],
                "price": dish["price"],
                "quantity": quantity,
                "subtotal": subtotal,
            }
        )

    if not order_items:
        return jsonify({"message": "购物车为空"}), 400

    order = {
        "id": len(orders) + 1,
        "customer": session.get("username", "顾客"),
        "items": order_items,
        "total": total,
        "status": "已下单",
        "created_at": datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
    }
    orders.append(order)
    return jsonify(order), 201


@app.get("/api/orders")
@admin_required
def list_orders():
    return jsonify(list(reversed(orders)))


@app.get("/api/my/orders")
@login_required
def list_my_orders():
    username = session.get("username")
    my_orders = [order for order in orders if order.get("customer") == username]
    return jsonify(list(reversed(my_orders)))


@app.post("/api/ai/chat")
def ai_chat():
    data = request.get_json(silent=True) or {}
    message = data.get("message", "").strip()

    if not message:
        return jsonify({"message": "请输入你的点餐需求"}), 400

    api_key = os.environ.get("ZHIPU_API_KEY", "").strip()
    if not api_key:
        return jsonify({"reply": "智谱 API Key 还没有配置。请先在服务器环境变量里设置 ZHIPU_API_KEY。"})

    menu_text = "\n".join(
        f"- {dish['name']}：{dish['category']}，￥{dish['price']}，{dish['description']}"
        for dish in MENU
    )
    payload = {
        "model": os.environ.get("ZHIPU_MODEL", "glm-4-flash"),
        "messages": [
            {
                "role": "system",
                "content": (
                    "你是拾味小馆的 AI 点餐助手。你只围绕本店菜单推荐菜品，"
                    "需要根据用户的人数、预算、口味、忌口进行搭配，并给出总价估算。"
                    "回复要简洁、亲切，适合手机点餐页面展示。\n\n"
                    f"本店菜单：\n{menu_text}"
                ),
            },
            {"role": "user", "content": message},
        ],
        "temperature": 0.7,
        "stream": False,
    }

    req = urllib.request.Request(
        "https://open.bigmodel.cn/api/paas/v4/chat/completions",
        data=json.dumps(payload).encode("utf-8"),
        headers={
            "Authorization": f"Bearer {api_key}",
            "Content-Type": "application/json",
        },
        method="POST",
    )

    try:
        with urllib.request.urlopen(req, timeout=30) as response:
            result = json.loads(response.read().decode("utf-8"))
    except urllib.error.HTTPError as exc:
        detail = exc.read().decode("utf-8", errors="ignore")
        return jsonify({"message": f"智谱接口返回错误：{exc.code}", "detail": detail}), 502
    except Exception as exc:
        return jsonify({"message": f"AI 服务暂时不可用：{exc}"}), 502

    try:
        reply = result["choices"][0]["message"]["content"]
    except (KeyError, IndexError, TypeError):
        return jsonify({"message": "智谱接口返回格式异常", "detail": result}), 502

    return jsonify({"reply": reply})


@app.patch("/api/orders/<int:order_id>")
@admin_required
def update_order(order_id):
    data = request.get_json(silent=True) or {}
    status = data.get("status")
    allowed_statuses = {"已下单", "制作中", "已完成", "已取消"}

    if status not in allowed_statuses:
        return jsonify({"message": "订单状态不正确"}), 400

    for order in orders:
        if order["id"] == order_id:
            order["status"] = status
            return jsonify(order)

    return jsonify({"message": "订单不存在"}), 404


init_db()


if __name__ == "__main__":
    port = int(os.environ.get("PORT", 5000))
    app.run(host="0.0.0.0", port=port, debug=False, use_reloader=False)
