import base64
from datetime import date, datetime, timedelta
import json
import os
import sqlite3
import urllib.error
import urllib.request
from functools import wraps

from flask import Flask, jsonify, redirect, render_template, request, session, url_for
from werkzeug.security import check_password_hash, generate_password_hash
from werkzeug.utils import secure_filename


app = Flask(__name__)
app.secret_key = os.environ.get("SECRET_KEY", "dev-secret-key-change-me")
DB_PATH = os.path.join(app.root_path, "order_app.db")
UPLOAD_FOLDER = os.path.join(app.root_path, "static", "uploads")
os.makedirs(UPLOAD_FOLDER, exist_ok=True)


MENU = [
    {"id": 1, "name": "招牌牛肉面", "category": "主食", "price": 28, "tag": "热卖", "sales": 386, "description": "慢炖牛腱、手工宽面、浓郁红汤", "image": "https://images.unsplash.com/photo-1555126634-323283e090fa?auto=format&fit=crop&w=640&q=80"},
    {"id": 2, "name": "黑椒鸡排饭", "category": "主食", "price": 32, "tag": "推荐", "sales": 291, "description": "现煎鸡排配黑椒汁，米饭软糯", "image": "https://images.unsplash.com/photo-1603133872878-684f208fb84b?auto=format&fit=crop&w=640&q=80"},
    {"id": 3, "name": "番茄炒蛋饭", "category": "主食", "price": 22, "tag": "经典", "sales": 214, "description": "酸甜番茄、滑嫩鸡蛋，家常口味", "image": "https://images.unsplash.com/photo-1512058564366-18510be2db19?auto=format&fit=crop&w=640&q=80"},
    {"id": 4, "name": "宫保鸡丁饭", "category": "主食", "price": 29, "tag": "下饭", "sales": 302, "description": "鸡丁鲜嫩，花生香脆，微辣酸甜", "image": "https://images.unsplash.com/photo-1563379091339-03246963d29a?auto=format&fit=crop&w=640&q=80"},
    {"id": 5, "name": "香菇滑鸡饭", "category": "主食", "price": 30, "tag": "鲜香", "sales": 227, "description": "香菇浓香，鸡腿肉滑嫩多汁", "image": "https://images.unsplash.com/photo-1516684732162-798a0062be99?auto=format&fit=crop&w=640&q=80"},
    {"id": 6, "name": "台式卤肉饭", "category": "主食", "price": 26, "tag": "经典", "sales": 354, "description": "卤肉酱香浓郁，配溏心蛋更满足", "image": "https://images.unsplash.com/photo-1546069901-d5bfd2cbfb1f?auto=format&fit=crop&w=640&q=80"},
    {"id": 7, "name": "咖喱鸡排饭", "category": "主食", "price": 31, "tag": "浓香", "sales": 187, "description": "金黄咖喱配酥嫩鸡排，香气足", "image": "https://images.unsplash.com/photo-1455619452474-d2be8b1e70cd?auto=format&fit=crop&w=640&q=80"},
    {"id": 8, "name": "酸菜鱼米饭", "category": "主食", "price": 36, "tag": "开胃", "sales": 266, "description": "鱼片嫩滑，酸菜爽脆，汤底鲜亮", "image": "https://images.unsplash.com/photo-1617093727343-374698b1b08d?auto=format&fit=crop&w=640&q=80"},
    {"id": 9, "name": "麻辣香锅饭", "category": "主食", "price": 34, "tag": "重口", "sales": 318, "description": "多种荤素小炒，麻辣鲜香很过瘾", "image": "https://images.unsplash.com/photo-1582878826629-29b7ad1cdc43?auto=format&fit=crop&w=640&q=80"},
    {"id": 10, "name": "青椒肉丝饭", "category": "主食", "price": 27, "tag": "家常", "sales": 176, "description": "肉丝滑嫩，青椒清香，米饭搭档", "image": "https://images.unsplash.com/photo-1559847844-5315695dadae?auto=format&fit=crop&w=640&q=80"},
    {"id": 11, "name": "照烧鸡腿饭", "category": "主食", "price": 33, "tag": "人气", "sales": 339, "description": "照烧汁浓郁，鸡腿肉鲜嫩带焦香", "image": "https://images.unsplash.com/photo-1532550907401-a500c9a57435?auto=format&fit=crop&w=640&q=80"},
    {"id": 12, "name": "虾仁炒饭", "category": "主食", "price": 30, "tag": "鲜香", "sales": 203, "description": "粒粒分明，虾仁弹嫩，锅气十足", "image": "https://images.unsplash.com/photo-1603133872878-684f208fb84b?auto=format&fit=crop&w=640&q=80"},
    {"id": 13, "name": "牛肉炒河粉", "category": "主食", "price": 29, "tag": "锅气", "sales": 241, "description": "河粉爽滑，牛肉鲜嫩，酱香浓", "image": "https://images.unsplash.com/photo-1612929633738-8fe44f7ec841?auto=format&fit=crop&w=640&q=80"},
    {"id": 14, "name": "三鲜馄饨", "category": "主食", "price": 24, "tag": "清爽", "sales": 168, "description": "皮薄馅足，汤头清鲜，暖胃舒服", "image": "https://images.unsplash.com/photo-1605478371310-a9f1e96b4ff4?auto=format&fit=crop&w=640&q=80"},
    {"id": 15, "name": "蒜蓉生菜", "category": "小菜", "price": 16, "tag": "清爽", "sales": 128, "description": "大火快炒，蒜香清脆", "image": "https://images.unsplash.com/photo-1546069901-ba9599a7e63c?auto=format&fit=crop&w=640&q=80"},
    {"id": 16, "name": "香辣鸡翅", "category": "小菜", "price": 24, "tag": "微辣", "sales": 176, "description": "外皮焦香，辣度温和", "image": "https://images.unsplash.com/photo-1567620832903-9fc6debc209f?auto=format&fit=crop&w=640&q=80"},
    {"id": 17, "name": "凉拌黄瓜", "category": "小菜", "price": 12, "tag": "爽口", "sales": 221, "description": "清脆黄瓜，蒜香酸辣，解腻刚好", "image": "https://images.unsplash.com/photo-1604909052743-94e838986d24?auto=format&fit=crop&w=640&q=80"},
    {"id": 18, "name": "酸辣土豆丝", "category": "小菜", "price": 13, "tag": "开胃", "sales": 195, "description": "细切土豆丝，酸辣脆爽", "image": "https://images.unsplash.com/photo-1518977676601-b53f82aba655?auto=format&fit=crop&w=640&q=80"},
    {"id": 19, "name": "卤蛋", "category": "小菜", "price": 6, "tag": "加料", "sales": 420, "description": "老卤入味，蛋香浓郁", "image": "https://images.unsplash.com/photo-1587486913049-53fc88980cfc?auto=format&fit=crop&w=640&q=80"},
    {"id": 20, "name": "手撕包菜", "category": "小菜", "price": 15, "tag": "锅气", "sales": 151, "description": "包菜脆甜，干椒炝香", "image": "https://images.unsplash.com/photo-1566385101042-1a0aa0c1268c?auto=format&fit=crop&w=640&q=80"},
    {"id": 21, "name": "红油抄手", "category": "小菜", "price": 18, "tag": "微辣", "sales": 234, "description": "抄手饱满，红油香而不燥", "image": "https://images.unsplash.com/photo-1496116218417-1a781b1c416c?auto=format&fit=crop&w=640&q=80"},
    {"id": 22, "name": "黄金小酥肉", "category": "小菜", "price": 22, "tag": "酥脆", "sales": 278, "description": "现炸酥肉，椒盐香气足", "image": "https://images.unsplash.com/photo-1625938144755-652e08e359b7?auto=format&fit=crop&w=640&q=80"},
    {"id": 23, "name": "蒜香排骨", "category": "小菜", "price": 26, "tag": "硬菜", "sales": 143, "description": "排骨外酥里嫩，蒜香浓郁", "image": "https://images.unsplash.com/photo-1544025162-d76694265947?auto=format&fit=crop&w=640&q=80"},
    {"id": 24, "name": "藤椒豆腐", "category": "小菜", "price": 14, "tag": "鲜麻", "sales": 132, "description": "嫩豆腐配藤椒汁，清爽鲜麻", "image": "https://images.unsplash.com/photo-1604908176997-125f25cc6f3d?auto=format&fit=crop&w=640&q=80"},
    {"id": 25, "name": "柠檬红茶", "category": "饮品", "price": 12, "tag": "冰饮", "sales": 242, "description": "鲜切柠檬，茶香清亮", "image": "https://images.unsplash.com/photo-1556679343-c7306c1976bc?auto=format&fit=crop&w=640&q=80"},
    {"id": 26, "name": "鲜榨橙汁", "category": "饮品", "price": 16, "tag": "鲜榨", "sales": 119, "description": "现榨橙汁，无额外加糖", "image": "https://images.unsplash.com/photo-1621506289937-a8e4df240d0b?auto=format&fit=crop&w=640&q=80"},
    {"id": 27, "name": "茉莉奶绿", "category": "饮品", "price": 15, "tag": "奶茶", "sales": 211, "description": "茉莉茶香清雅，奶感顺滑", "image": "https://images.unsplash.com/photo-1558857563-b371033873b8?auto=format&fit=crop&w=640&q=80"},
    {"id": 28, "name": "杨枝甘露", "category": "饮品", "price": 18, "tag": "甜品", "sales": 166, "description": "芒果、西柚、椰乳，清甜浓郁", "image": "https://images.unsplash.com/photo-1572490122747-3968b75cc699?auto=format&fit=crop&w=640&q=80"},
    {"id": 29, "name": "冰美式", "category": "饮品", "price": 13, "tag": "咖啡", "sales": 98, "description": "清爽提神，低糖低负担", "image": "https://images.unsplash.com/photo-1461023058943-07fcbe16d735?auto=format&fit=crop&w=640&q=80"},
    {"id": 30, "name": "西瓜汁", "category": "饮品", "price": 14, "tag": "鲜榨", "sales": 155, "description": "新鲜西瓜现榨，清凉解渴", "image": "https://images.unsplash.com/photo-1525385133512-2f3bdd039054?auto=format&fit=crop&w=640&q=80"},
    {"id": 31, "name": "桂花酸梅汤", "category": "饮品", "price": 12, "tag": "解腻", "sales": 188, "description": "酸甜回甘，桂花清香", "image": "https://images.unsplash.com/photo-1502741224143-90386d7f8c82?auto=format&fit=crop&w=640&q=80"},
    {"id": 32, "name": "蜂蜜柚子茶", "category": "饮品", "price": 14, "tag": "温润", "sales": 126, "description": "柚香清新，冷热皆宜", "image": "https://images.unsplash.com/photo-1544145945-f90425340c7e?auto=format&fit=crop&w=640&q=80"},
    {"id": 33, "name": "百香果气泡水", "category": "饮品", "price": 16, "tag": "气泡", "sales": 139, "description": "果香明亮，气泡清爽", "image": "https://images.unsplash.com/photo-1513558161293-cdaf765ed2fd?auto=format&fit=crop&w=640&q=80"},
    {"id": 34, "name": "原味豆浆", "category": "饮品", "price": 8, "tag": "热饮", "sales": 203, "description": "豆香醇厚，早餐和正餐都合适", "image": "https://images.unsplash.com/photo-1622484211148-8a628b05edc1?auto=format&fit=crop&w=640&q=80"},
]

CATEGORY_ORDER = ["主食", "小菜", "饮品"]
orders = []


FALLBACK_IMAGES = {
    "主食": "https://images.unsplash.com/photo-1546069901-d5bfd2cbfb1f?auto=format&fit=crop&w=640&q=80",
    "小菜": "https://images.unsplash.com/photo-1546069901-ba9599a7e63c?auto=format&fit=crop&w=640&q=80",
    "饮品": "https://images.unsplash.com/photo-1544145945-f90425340c7e?auto=format&fit=crop&w=640&q=80",
}

MENU = [
    {
        "id": 101,
        "name": "土豆炖豆角",
        "category": "现做炖菜",
        "price": 20,
        "tag": "锅气现炖",
        "sales": 0,
        "description": "土豆绵软，豆角入味，东北家常炖菜",
        "image": "https://images.unsplash.com/photo-1604908176997-125f25cc6f3d?auto=format&fit=crop&w=640&q=80",
        "options": [
            {"id": "fentiao", "name": "加粉条", "price": 5},
            {"id": "paigu", "name": "加排骨", "price": 10},
        ],
    },
    {
        "id": 102,
        "name": "白菜炖豆腐",
        "category": "现做炖菜",
        "price": 10,
        "tag": "清爽热乎",
        "sales": 0,
        "description": "白菜清甜，豆腐嫩滑，汤汁鲜暖",
        "image": "https://images.unsplash.com/photo-1512621776951-a57141f2eefd?auto=format&fit=crop&w=640&q=80",
        "options": [{"id": "fentiao", "name": "加粉条", "price": 5}],
    },
    {
        "id": 103,
        "name": "小鸡炖土豆",
        "category": "现做炖菜",
        "price": 30,
        "tag": "招牌硬菜",
        "sales": 0,
        "description": "鸡肉鲜嫩，土豆吸满汤汁，适合配米饭",
        "image": "https://images.unsplash.com/photo-1604909052743-94e838986d24?auto=format&fit=crop&w=640&q=80",
        "options": [],
    },
    {
        "id": 104,
        "name": "炒干豆腐",
        "category": "精品炒菜",
        "price": 15,
        "tag": "家常小炒",
        "sales": 0,
        "description": "干豆腐软韧入味，大火快炒更香",
        "image": "https://images.unsplash.com/photo-1604908176997-125f25cc6f3d?auto=format&fit=crop&w=640&q=80",
        "options": [{"id": "rouding", "name": "加肉丁", "price": 5}],
    },
    {
        "id": 105,
        "name": "豆腐炒鸡蛋",
        "category": "精品炒菜",
        "price": 13,
        "tag": "鲜嫩",
        "sales": 0,
        "description": "豆腐细嫩，鸡蛋香软，口味清爽",
        "image": "https://images.unsplash.com/photo-1582169296194-e4d644c48063?auto=format&fit=crop&w=640&q=80",
        "options": [{"id": "rouding", "name": "加肉丁", "price": 5}],
    },
    {
        "id": 106,
        "name": "韭菜炒鸡蛋",
        "category": "精品炒菜",
        "price": 15,
        "tag": "鲜香",
        "sales": 0,
        "description": "韭菜鲜香，鸡蛋蓬松，现炒上桌",
        "image": "https://images.unsplash.com/photo-1512058564366-18510be2db19?auto=format&fit=crop&w=640&q=80",
        "options": [{"id": "rouding", "name": "加肉丁", "price": 5}],
    },
    {
        "id": 107,
        "name": "土豆丝炒鸡蛋",
        "category": "精品炒菜",
        "price": 13,
        "tag": "下饭",
        "sales": 0,
        "description": "土豆丝爽口，鸡蛋香软，家常味十足",
        "image": "https://images.unsplash.com/photo-1518977676601-b53f82aba655?auto=format&fit=crop&w=640&q=80",
        "options": [{"id": "rouding", "name": "加肉丁", "price": 5}],
    },
    {
        "id": 108,
        "name": "蒜苔炒肉",
        "category": "精品炒菜",
        "price": 18,
        "tag": "人气",
        "sales": 0,
        "description": "蒜苔脆香，肉片鲜嫩，米饭好搭档",
        "image": "https://images.unsplash.com/photo-1559847844-5315695dadae?auto=format&fit=crop&w=640&q=80",
        "options": [],
    },
    {
        "id": 109,
        "name": "现焖米饭",
        "category": "主食",
        "price": 3,
        "tag": "现焖",
        "sales": 0,
        "description": "一人份现焖米饭，颗粒饱满",
        "image": "https://images.unsplash.com/photo-1536304993881-ff6e9eefa2a6?auto=format&fit=crop&w=640&q=80",
        "options": [],
    },
    {
        "id": 110,
        "name": "烀饼",
        "category": "主食",
        "price": 10,
        "tag": "炖菜限定",
        "sales": 0,
        "description": "炖菜点单推荐搭配，吸汤更香",
        "image": "https://images.unsplash.com/photo-1578985545062-69928b1d9587?auto=format&fit=crop&w=640&q=80",
        "options": [],
    },
    {
        "id": 111,
        "name": "可口可乐",
        "category": "饮品",
        "price": 4,
        "tag": "冰爽",
        "sales": 0,
        "description": "经典汽水，冰镇更爽",
        "image": "https://images.unsplash.com/photo-1622483767028-3f66f32aef97?auto=format&fit=crop&w=640&q=80",
        "options": [],
    },
    {
        "id": 112,
        "name": "芬达",
        "category": "饮品",
        "price": 4,
        "tag": "橙味",
        "sales": 0,
        "description": "橙味汽水，甜爽解腻",
        "image": "https://images.unsplash.com/photo-1621506289937-a8e4df240d0b?auto=format&fit=crop&w=640&q=80",
        "options": [],
    },
    {
        "id": 113,
        "name": "雪碧",
        "category": "饮品",
        "price": 4,
        "tag": "清爽",
        "sales": 0,
        "description": "柠檬味汽水，清爽提神",
        "image": "https://images.unsplash.com/photo-1544145945-f90425340c7e?auto=format&fit=crop&w=640&q=80",
        "options": [],
    },
    {
        "id": 114,
        "name": "大窑",
        "category": "饮品",
        "price": 7,
        "tag": "大瓶",
        "sales": 0,
        "description": "东北餐桌经典汽水，分量更足",
        "image": "https://images.unsplash.com/photo-1513558161293-cdaf765ed2fd?auto=format&fit=crop&w=640&q=80",
        "options": [],
    },
    {
        "id": 115,
        "name": "美年达",
        "category": "饮品",
        "price": 4,
        "tag": "果味",
        "sales": 0,
        "description": "果味汽水，适合搭配热菜",
        "image": "https://images.unsplash.com/photo-1621506289937-a8e4df240d0b?auto=format&fit=crop&w=640&q=80",
        "options": [],
    },
]

CATEGORY_ORDER = ["现做炖菜", "精品炒菜", "主食", "饮品"]
FALLBACK_IMAGES = {
    "现做炖菜": "https://images.unsplash.com/photo-1604908176997-125f25cc6f3d?auto=format&fit=crop&w=640&q=80",
    "精品炒菜": "https://images.unsplash.com/photo-1512058564366-18510be2db19?auto=format&fit=crop&w=640&q=80",
    "主食": "https://images.unsplash.com/photo-1536304993881-ff6e9eefa2a6?auto=format&fit=crop&w=640&q=80",
    "饮品": "https://images.unsplash.com/photo-1622483767028-3f66f32aef97?auto=format&fit=crop&w=640&q=80",
}


def menu_item(dish_id):
    return next((dish for dish in MENU if dish["id"] == int(dish_id)), None)


def menu_with_sales():
    with get_db() as conn:
        rows = conn.execute("SELECT dish_id, sales FROM dish_stats").fetchall()
    sales_by_id = {row["dish_id"]: row["sales"] for row in rows}
    return [{**dish, "sales": sales_by_id.get(dish["id"], dish["sales"])} for dish in MENU]


def reward_for_streak(streak):
    if streak <= 7:
        return streak
    return ((streak - 8) % 6) + 2


def parse_iso_date(value):
    if not value:
        return None
    try:
        return datetime.strptime(value, "%Y-%m-%d").date()
    except ValueError:
        return None


def get_db():
    conn = sqlite3.connect(DB_PATH)
    conn.row_factory = sqlite3.Row
    return conn


def ensure_column(conn, table, column, definition):
    columns = [row["name"] for row in conn.execute(f"PRAGMA table_info({table})")]
    if column not in columns:
        conn.execute(f"ALTER TABLE {table} ADD COLUMN {column} {definition}")


def save_avatar(file_storage):
    if not file_storage or not file_storage.filename:
        return ""
    filename = secure_filename(file_storage.filename)
    ext = os.path.splitext(filename)[1].lower()
    if ext not in {".jpg", ".jpeg", ".png", ".gif", ".webp"}:
        return ""
    saved_name = f"avatar_{int(datetime.now().timestamp() * 1000)}{ext}"
    file_storage.save(os.path.join(UPLOAD_FOLDER, saved_name))
    return url_for("static", filename=f"uploads/{saved_name}")


def init_db():
    with get_db() as conn:
        conn.execute(
            """
            CREATE TABLE IF NOT EXISTS users (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                username TEXT NOT NULL UNIQUE,
                nickname TEXT,
                avatar_url TEXT,
                password_hash TEXT NOT NULL,
                role TEXT NOT NULL DEFAULT 'customer',
                points INTEGER NOT NULL DEFAULT 0,
                checkin_streak INTEGER NOT NULL DEFAULT 0,
                last_checkin_date TEXT,
                created_at TEXT NOT NULL
            )
            """
        )
        ensure_column(conn, "users", "nickname", "TEXT")
        ensure_column(conn, "users", "avatar_url", "TEXT")
        ensure_column(conn, "users", "points", "INTEGER NOT NULL DEFAULT 0")
        ensure_column(conn, "users", "checkin_streak", "INTEGER NOT NULL DEFAULT 0")
        ensure_column(conn, "users", "last_checkin_date", "TEXT")
        conn.execute(
            """
            CREATE TABLE IF NOT EXISTS coupons (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                user_id INTEGER NOT NULL,
                title TEXT NOT NULL,
                amount REAL NOT NULL,
                min_amount REAL NOT NULL DEFAULT 0,
                status TEXT NOT NULL DEFAULT 'unused',
                source TEXT NOT NULL DEFAULT 'merchant',
                created_at TEXT NOT NULL,
                used_at TEXT,
                order_id INTEGER,
                FOREIGN KEY(user_id) REFERENCES users(id)
            )
            """
        )
        ensure_column(conn, "coupons", "source", "TEXT NOT NULL DEFAULT 'merchant'")
        conn.execute(
            """
            CREATE TABLE IF NOT EXISTS orders (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                user_id INTEGER NOT NULL,
                customer TEXT NOT NULL,
                total REAL NOT NULL,
                discount REAL NOT NULL DEFAULT 0,
                payable REAL NOT NULL,
                coupon_id INTEGER,
                address TEXT,
                phone TEXT,
                remark TEXT,
                estimated_time TEXT,
                delivery_method TEXT NOT NULL DEFAULT 'delivery',
                status TEXT NOT NULL DEFAULT '已下单',
                customer_deleted INTEGER NOT NULL DEFAULT 0,
                admin_deleted INTEGER NOT NULL DEFAULT 0,
                created_at TEXT NOT NULL,
                FOREIGN KEY(user_id) REFERENCES users(id),
                FOREIGN KEY(coupon_id) REFERENCES coupons(id)
            )
            """
        )
        ensure_column(conn, "orders", "remark", "TEXT")
        ensure_column(conn, "orders", "estimated_time", "TEXT")
        ensure_column(conn, "orders", "customer_deleted", "INTEGER NOT NULL DEFAULT 0")
        ensure_column(conn, "orders", "admin_deleted", "INTEGER NOT NULL DEFAULT 0")
        conn.execute(
            """
            CREATE TABLE IF NOT EXISTS order_items (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                order_id INTEGER NOT NULL,
                dish_id INTEGER NOT NULL,
                name TEXT NOT NULL,
                price REAL NOT NULL,
                quantity INTEGER NOT NULL,
                subtotal REAL NOT NULL,
                image TEXT,
                options TEXT,
                FOREIGN KEY(order_id) REFERENCES orders(id)
            )
            """
        )
        ensure_column(conn, "order_items", "options", "TEXT")
        conn.execute(
            """
            CREATE TABLE IF NOT EXISTS dish_stats (
                dish_id INTEGER PRIMARY KEY,
                sales INTEGER NOT NULL DEFAULT 0
            )
            """
        )
        conn.execute(
            """
            CREATE TABLE IF NOT EXISTS messages (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                user_id INTEGER NOT NULL,
                sender TEXT NOT NULL,
                body TEXT NOT NULL,
                created_at TEXT NOT NULL,
                FOREIGN KEY(user_id) REFERENCES users(id)
            )
            """
        )
        for dish in MENU:
            conn.execute(
                "INSERT OR IGNORE INTO dish_stats (dish_id, sales) VALUES (?, ?)",
                (dish["id"], dish["sales"]),
            )
            conn.execute(
                "UPDATE dish_stats SET sales = ? WHERE dish_id = ? AND sales < ?",
                (dish["sales"], dish["id"], dish["sales"]),
            )
        admin = conn.execute("SELECT id FROM users WHERE username = ?", ("admin",)).fetchone()
        if admin is None:
            conn.execute(
                "INSERT INTO users (username, password_hash, role, created_at) VALUES (?, ?, ?, ?)",
                (
                    "admin",
                    generate_password_hash("admin12345"),
                    "admin",
                    datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
                ),
            )
        else:
            admin_hash = conn.execute(
                "SELECT password_hash FROM users WHERE username = ?",
                ("admin",),
            ).fetchone()["password_hash"]
            if check_password_hash(admin_hash, "admin123"):
                conn.execute(
                    "UPDATE users SET password_hash = ? WHERE username = ?",
                    (generate_password_hash("admin12345"), "admin"),
                )


def current_user():
    user_id = session.get("user_id")
    if not user_id:
        return None
    with get_db() as conn:
        return conn.execute(
            "SELECT id, username, nickname, avatar_url, role, points, checkin_streak, last_checkin_date FROM users WHERE id = ?",
            (user_id,),
        ).fetchone()


def public_user(user):
    if user is None:
        return None
    return {
        "id": user["id"],
        "username": user["username"],
        "nickname": user["nickname"] if "nickname" in user.keys() and user["nickname"] else user["username"],
        "avatar_url": user["avatar_url"] if "avatar_url" in user.keys() else "",
        "role": user["role"],
        "points": user["points"] if "points" in user.keys() else 0,
    }


def register_customer(username, password, confirm_password, nickname="", avatar_url=""):
    if len(username) < 3:
        return None, "用户名至少 3 个字符"
    if len(password) < 6:
        return None, "密码至少 6 位"
    if password != confirm_password:
        return None, "两次输入的密码不一致"

    try:
        with get_db() as conn:
            cursor = conn.execute(
                "INSERT INTO users (username, nickname, avatar_url, password_hash, role, created_at) VALUES (?, ?, ?, ?, ?, ?)",
                (
                    username,
                    nickname.strip() or username,
                    avatar_url,
                    generate_password_hash(password),
                    "customer",
                    datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
                ),
            )
            return {
                "id": cursor.lastrowid,
                "username": username,
                "nickname": nickname.strip() or username,
                "avatar_url": avatar_url,
                "role": "customer",
            }, ""
    except sqlite3.IntegrityError:
        return None, "这个用户名已经被注册"


def authenticate(username, password):
    with get_db() as conn:
        user = conn.execute(
            "SELECT id, username, nickname, avatar_url, password_hash, role FROM users WHERE username = ?",
            (username,),
        ).fetchone()

    if user is None or not check_password_hash(user["password_hash"], password):
        return None
    return user


def remember_user(user):
    session["user_id"] = user["id"]
    session["username"] = user["username"]
    session["role"] = user["role"]


def serialize_order(row, items):
    return {
        "id": row["id"],
        "customer": row["customer"],
        "items": items,
        "total": row["total"],
        "discount": row["discount"],
        "payable": row["payable"],
        "coupon_id": row["coupon_id"],
        "address": row["address"],
        "phone": row["phone"],
        "remark": row["remark"],
        "estimated_time": row["estimated_time"],
        "delivery_method": row["delivery_method"],
        "status": row["status"],
        "created_at": row["created_at"],
    }


def fetch_orders(where="", params=()):
    with get_db() as conn:
        rows = conn.execute(
            f"SELECT * FROM orders {where} ORDER BY id DESC",
            params,
        ).fetchall()
        result = []
        for row in rows:
            item_rows = conn.execute(
                "SELECT dish_id AS id, name, price, quantity, subtotal, image, options FROM order_items WHERE order_id = ?",
                (row["id"],),
            ).fetchall()
            items = []
            for item in item_rows:
                item_dict = dict(item)
                try:
                    item_dict["options"] = json.loads(item_dict.get("options") or "[]")
                except (TypeError, ValueError):
                    item_dict["options"] = []
                items.append(item_dict)
            result.append(serialize_order(row, items))
        return result


def serialize_coupon(row):
    return {
        "id": row["id"],
        "user_id": row["user_id"],
        "username": row["username"] if "username" in row.keys() else None,
        "title": row["title"],
        "amount": row["amount"],
        "min_amount": row["min_amount"],
        "status": row["status"],
        "source": row["source"] if "source" in row.keys() else "merchant",
        "created_at": row["created_at"],
        "used_at": row["used_at"],
        "order_id": row["order_id"],
    }


def serialize_message(row):
    return {
        "id": row["id"],
        "user_id": row["user_id"],
        "sender": row["sender"],
        "body": row["body"],
        "created_at": row["created_at"],
    }


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
    menu = menu_with_sales()
    categories = [category for category in CATEGORY_ORDER if any(d["category"] == category for d in menu)]
    return render_template("index.html", menu=menu, categories=categories, user=current_user())


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
    if request.form:
        data = request.form
        avatar_url = save_avatar(request.files.get("avatar"))
    else:
        data = request.get_json(silent=True) or {}
        avatar_url = ""
    user, error = register_customer(
        data.get("username", "").strip(),
        data.get("password", ""),
        data.get("confirm_password", ""),
        data.get("nickname", "").strip(),
        avatar_url,
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


@app.patch("/api/my/profile")
@login_required
def update_profile():
    user_id = session["user_id"]
    nickname = request.form.get("nickname", "").strip()
    avatar_url = save_avatar(request.files.get("avatar"))

    if not nickname and not avatar_url:
        return jsonify({"message": "请填写昵称或上传头像"}), 400

    with get_db() as conn:
        if nickname:
            conn.execute("UPDATE users SET nickname = ? WHERE id = ?", (nickname, user_id))
        if avatar_url:
            conn.execute("UPDATE users SET avatar_url = ? WHERE id = ?", (avatar_url, user_id))
        user = conn.execute(
            "SELECT id, username, nickname, avatar_url, role, points FROM users WHERE id = ?",
            (user_id,),
        ).fetchone()

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
    coupon_id = data.get("coupon_id")
    phone = data.get("phone", "").strip()
    remark = data.get("remark", "").strip()
    estimated_time = data.get("estimated_time", "").strip()
    delivery_method = "dine_in"

    order_items = []
    total = 0
    menu_by_id = {dish["id"]: dish for dish in MENU}

    for item in items:
        dish = menu_by_id.get(item.get("id"))
        quantity = int(item.get("quantity", 0))
        if dish is None or quantity <= 0:
            continue

        option_ids = {str(option_id) for option_id in item.get("options", [])}
        selected_options = [
            option for option in dish.get("options", [])
            if str(option.get("id")) in option_ids
        ]
        option_total = sum(float(option["price"]) for option in selected_options)
        unit_price = float(dish["price"]) + option_total
        display_name = dish["name"]
        if selected_options:
            display_name = "{}（{}）".format(
                dish["name"],
                "、".join(option["name"] for option in selected_options),
            )
        subtotal = unit_price * quantity
        total += subtotal
        order_items.append(
            {
                "id": dish["id"],
                "name": display_name,
                "price": unit_price,
                "quantity": quantity,
                "subtotal": subtotal,
                "image": dish["image"],
                "options": selected_options,
            }
        )

    if not order_items:
        return jsonify({"message": "购物车为空"}), 400

    user_id = session["user_id"]
    discount = 0
    coupon_row = None
    now = datetime.now().strftime("%Y-%m-%d %H:%M:%S")

    with get_db() as conn:
        if coupon_id:
            coupon_row = conn.execute(
                """
                SELECT * FROM coupons
                WHERE id = ? AND user_id = ? AND status = 'unused'
                """,
                (coupon_id, user_id),
            ).fetchone()
            if coupon_row is None:
                return jsonify({"message": "优惠券不可用"}), 400
            if total < coupon_row["min_amount"]:
                return jsonify({"message": "未达到优惠券使用门槛"}), 400
            discount = min(float(coupon_row["amount"]), float(total))

        payable = max(float(total) - float(discount), 0)
        cursor = conn.execute(
            """
            INSERT INTO orders
            (user_id, customer, total, discount, payable, coupon_id, address, phone, remark, estimated_time, delivery_method, status, created_at)
            VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
            """,
            (
                user_id,
                session.get("username", "顾客"),
                total,
                discount,
                payable,
                coupon_id if coupon_row else None,
                "",
                phone,
                remark,
                estimated_time,
                delivery_method,
                "已下单",
                now,
            ),
        )
        order_id = cursor.lastrowid
        for item in order_items:
            conn.execute(
                """
                INSERT INTO order_items
                (order_id, dish_id, name, price, quantity, subtotal, image, options)
                VALUES (?, ?, ?, ?, ?, ?, ?, ?)
                """,
                (
                    order_id,
                    item["id"],
                    item["name"],
                    item["price"],
                    item["quantity"],
                    item["subtotal"],
                    item["image"],
                    json.dumps(item["options"], ensure_ascii=False),
                ),
            )
            conn.execute("INSERT OR IGNORE INTO dish_stats (dish_id, sales) VALUES (?, 0)", (item["id"],))
            conn.execute(
                "UPDATE dish_stats SET sales = sales + ? WHERE dish_id = ?",
                (item["quantity"], item["id"]),
            )
        if coupon_row:
            conn.execute(
                "UPDATE coupons SET status = 'used', used_at = ?, order_id = ? WHERE id = ?",
                (now, order_id, coupon_row["id"]),
            )

    order = fetch_orders("WHERE id = ?", (order_id,))[0]
    return jsonify(order), 201


@app.get("/api/orders")
@admin_required
def list_orders():
    return jsonify(fetch_orders("WHERE admin_deleted = 0"))


@app.get("/api/my/orders")
@login_required
def list_my_orders():
    return jsonify(fetch_orders("WHERE user_id = ? AND customer_deleted = 0", (session["user_id"],)))


@app.get("/api/my/coupons")
@login_required
def list_my_coupons():
    min_total = float(request.args.get("total", 0) or 0)
    include_all = request.args.get("all") == "1"
    status_filter = "" if include_all else "AND coupons.status = 'unused'"
    with get_db() as conn:
        rows = conn.execute(
            f"""
            SELECT coupons.*, users.username FROM coupons
            JOIN users ON users.id = coupons.user_id
            WHERE coupons.user_id = ? {status_filter}
            ORDER BY coupons.id DESC
            """,
            (session["user_id"],),
        ).fetchall()
    coupons = [serialize_coupon(row) for row in rows]
    for coupon in coupons:
        coupon["available"] = min_total >= coupon["min_amount"]
    return jsonify(coupons)


@app.get("/api/my/wallet")
@login_required
def my_wallet():
    user_id = session["user_id"]
    today_text = date.today().isoformat()
    with get_db() as conn:
        user = conn.execute(
            "SELECT points, checkin_streak, last_checkin_date FROM users WHERE id = ?",
            (user_id,),
        ).fetchone()
        coupons = conn.execute(
            """
            SELECT coupons.*, users.username FROM coupons
            JOIN users ON users.id = coupons.user_id
            WHERE coupons.user_id = ?
            ORDER BY coupons.id DESC
            """,
            (user_id,),
        ).fetchall()
    checked_today = user["last_checkin_date"] == today_text
    next_streak = user["checkin_streak"] if checked_today else user["checkin_streak"] + 1
    if user["last_checkin_date"]:
        last_day = parse_iso_date(user["last_checkin_date"])
        if not checked_today and last_day != date.today() - timedelta(days=1):
            next_streak = 1
    return jsonify(
        {
            "points": user["points"],
            "nickname": current_user()["nickname"] or current_user()["username"],
            "avatar_url": current_user()["avatar_url"] or "",
            "checkin_streak": user["checkin_streak"],
            "last_checkin_date": user["last_checkin_date"],
            "checked_today": checked_today,
            "next_reward": 0 if checked_today else reward_for_streak(next_streak),
            "coupons": [serialize_coupon(row) for row in coupons],
        }
    )


@app.post("/api/my/checkin")
@login_required
def checkin():
    user_id = session["user_id"]
    today = date.today()
    today_text = today.isoformat()
    with get_db() as conn:
        user = conn.execute(
            "SELECT points, checkin_streak, last_checkin_date FROM users WHERE id = ?",
            (user_id,),
        ).fetchone()
        if user["last_checkin_date"] == today_text:
            return jsonify(
                {
                    "message": "今天已经签到过了",
                    "points": user["points"],
                    "reward": 0,
                    "streak": user["checkin_streak"],
                    "checked_today": True,
                }
            )

        streak = 1
        if user["last_checkin_date"]:
            last_day = parse_iso_date(user["last_checkin_date"])
            if last_day == today - timedelta(days=1):
                streak = user["checkin_streak"] + 1

        reward = reward_for_streak(streak)
        points = user["points"] + reward
        conn.execute(
            """
            UPDATE users
            SET points = ?, checkin_streak = ?, last_checkin_date = ?
            WHERE id = ?
            """,
            (points, streak, today_text, user_id),
        )
    return jsonify(
        {
            "message": f"签到成功，获得 {reward} 积分",
            "points": points,
            "reward": reward,
            "streak": streak,
            "checked_today": True,
        }
    )


@app.post("/api/my/redeem")
@login_required
def redeem_points():
    user_id = session["user_id"]
    now = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    with get_db() as conn:
        user = conn.execute("SELECT points FROM users WHERE id = ?", (user_id,)).fetchone()
        if user["points"] < 20:
            return jsonify({"message": "积分不足，20 积分可兑换 5 元优惠券"}), 400
        conn.execute("UPDATE users SET points = points - 20 WHERE id = ?", (user_id,))
        cursor = conn.execute(
            """
            INSERT INTO coupons (user_id, title, amount, min_amount, status, source, created_at)
            VALUES (?, ?, ?, ?, 'unused', 'points', ?)
            """,
            (user_id, "20积分兑换券", 5, 0, now),
        )
        row = conn.execute(
            """
            SELECT coupons.*, users.username FROM coupons
            JOIN users ON users.id = coupons.user_id
            WHERE coupons.id = ?
            """,
            (cursor.lastrowid,),
        ).fetchone()
        points = conn.execute("SELECT points FROM users WHERE id = ?", (user_id,)).fetchone()["points"]
    coupon = serialize_coupon(row)
    coupon["available"] = True
    return jsonify({"message": "兑换成功，已放入卡包", "points": points, "coupon": coupon}), 201


@app.get("/api/admin/users")
@admin_required
def list_users():
    with get_db() as conn:
        rows = conn.execute(
            "SELECT id, username, nickname, role, created_at FROM users ORDER BY id DESC"
        ).fetchall()
    return jsonify([dict(row) for row in rows])


@app.delete("/api/admin/users/<int:user_id>")
@admin_required
def delete_user(user_id):
    with get_db() as conn:
        user = conn.execute(
            "SELECT id, username, role FROM users WHERE id = ?",
            (user_id,),
        ).fetchone()
        if user is None:
            return jsonify({"message": "用户不存在"}), 404
        if user["role"] == "admin":
            return jsonify({"message": "不能删除商家账号"}), 400
        conn.execute("DELETE FROM coupons WHERE user_id = ?", (user_id,))
        conn.execute("DELETE FROM messages WHERE user_id = ?", (user_id,))
        conn.execute("DELETE FROM users WHERE id = ?", (user_id,))
    return jsonify({"message": "用户登录信息已删除", "username": user["username"]})


@app.get("/api/my/messages")
@login_required
def list_my_messages():
    with get_db() as conn:
        rows = conn.execute(
            """
            SELECT id, user_id, sender, body, created_at
            FROM messages
            WHERE user_id = ?
            ORDER BY id ASC
            """,
            (session["user_id"],),
        ).fetchall()
    return jsonify([serialize_message(row) for row in rows])


@app.post("/api/my/messages")
@login_required
def create_my_message():
    data = request.get_json(silent=True) or {}
    body = data.get("body", "").strip()
    if not body:
        return jsonify({"message": "请输入消息内容"}), 400
    with get_db() as conn:
        cursor = conn.execute(
            """
            INSERT INTO messages (user_id, sender, body, created_at)
            VALUES (?, 'customer', ?, ?)
            """,
            (session["user_id"], body, datetime.now().strftime("%Y-%m-%d %H:%M:%S")),
        )
        row = conn.execute(
            "SELECT id, user_id, sender, body, created_at FROM messages WHERE id = ?",
            (cursor.lastrowid,),
        ).fetchone()
    return jsonify(serialize_message(row)), 201


@app.get("/api/admin/messages")
@admin_required
def list_admin_messages():
    with get_db() as conn:
        users = conn.execute(
            """
            SELECT users.id, users.username, users.nickname, users.avatar_url, users.role,
                   MAX(messages.id) AS last_message_id,
                   MAX(messages.created_at) AS last_message_at
            FROM users
            LEFT JOIN messages ON messages.user_id = users.id
            WHERE users.role != 'admin'
            GROUP BY users.id
            ORDER BY COALESCE(last_message_id, users.id) DESC
            """
        ).fetchall()
        threads = []
        for user in users:
            message_rows = conn.execute(
                """
                SELECT id, user_id, sender, body, created_at
                FROM messages
                WHERE user_id = ?
                ORDER BY id ASC
                """,
                (user["id"],),
            ).fetchall()
            threads.append(
                {
                    "user": public_user(user),
                    "messages": [serialize_message(row) for row in message_rows],
                    "last_message_at": user["last_message_at"],
                }
            )
    return jsonify({"threads": threads})


@app.post("/api/admin/messages")
@admin_required
def create_admin_message():
    data = request.get_json(silent=True) or {}
    user_id = int(data.get("user_id", 0) or 0)
    body = data.get("body", "").strip()
    if not user_id:
        return jsonify({"message": "请选择顾客"}), 400
    if not body:
        return jsonify({"message": "请输入回复内容"}), 400
    with get_db() as conn:
        user = conn.execute(
            "SELECT id FROM users WHERE id = ? AND role != 'admin'",
            (user_id,),
        ).fetchone()
        if user is None:
            return jsonify({"message": "用户不存在"}), 404
        cursor = conn.execute(
            """
            INSERT INTO messages (user_id, sender, body, created_at)
            VALUES (?, 'merchant', ?, ?)
            """,
            (user_id, body, datetime.now().strftime("%Y-%m-%d %H:%M:%S")),
        )
        row = conn.execute(
            "SELECT id, user_id, sender, body, created_at FROM messages WHERE id = ?",
            (cursor.lastrowid,),
        ).fetchone()
    return jsonify(serialize_message(row)), 201


@app.post("/api/admin/coupons")
@admin_required
def create_coupon():
    data = request.get_json(silent=True) or {}
    username = data.get("username", "").strip()
    title = data.get("title", "店铺优惠券").strip() or "店铺优惠券"
    amount = float(data.get("amount", 0) or 0)
    min_amount = float(data.get("min_amount", 0) or 0)

    if not username:
        return jsonify({"message": "请输入用户名"}), 400
    if amount <= 0:
        return jsonify({"message": "优惠金额必须大于 0"}), 400

    with get_db() as conn:
        user = conn.execute(
            "SELECT id, username FROM users WHERE username = ?",
            (username,),
        ).fetchone()
        if user is None:
            return jsonify({"message": "用户不存在"}), 404
        cursor = conn.execute(
            """
            INSERT INTO coupons (user_id, title, amount, min_amount, status, source, created_at)
            VALUES (?, ?, ?, ?, 'unused', 'merchant', ?)
            """,
            (
                user["id"],
                title,
                amount,
                min_amount,
                datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
            ),
        )
        row = conn.execute(
            """
            SELECT coupons.*, users.username FROM coupons
            JOIN users ON users.id = coupons.user_id
            WHERE coupons.id = ?
            """,
            (cursor.lastrowid,),
        ).fetchone()
    return jsonify(serialize_coupon(row)), 201


@app.post("/api/admin/password")
@admin_required
def update_admin_password():
    data = request.get_json(silent=True) or {}
    current_password = data.get("current_password", "")
    new_password = data.get("new_password", "")
    confirm_password = data.get("confirm_password", "")
    user = current_user()

    if not authenticate(user["username"], current_password):
        return jsonify({"message": "当前密码不正确"}), 400
    if len(new_password) < 6:
        return jsonify({"message": "新密码至少 6 位"}), 400
    if new_password != confirm_password:
        return jsonify({"message": "两次输入的新密码不一致"}), 400

    with get_db() as conn:
        conn.execute(
            "UPDATE users SET password_hash = ? WHERE id = ?",
            (generate_password_hash(new_password), user["id"]),
        )
    return jsonify({"message": "后台密码已更新"})


@app.post("/api/ai/recommend")
def ai_recommend():
    data = request.get_json(silent=True) or {}
    message = data.get("message", "").strip()
    blind_box = bool(data.get("blind_box"))
    text = message.lower()
    budget = None
    digits = "".join(char if char.isdigit() else " " for char in text).split()
    if digits:
        budget = max(int(number) for number in digits)

    if blind_box:
        selected_ids = [101, 109, 111]
    elif "辣" in message:
        selected_ids = [108, 109, 113]
    elif "清淡" in message or "不辣" in message:
        selected_ids = [102, 109, 113]
    elif "饮" in message or "喝" in message:
        selected_ids = [111, 112, 114]
    elif "两" in message or "2" in message:
        selected_ids = [103, 106, 109, 111]
    else:
        selected_ids = [101, 109, 111]

    selected = [menu_item(dish_id) for dish_id in selected_ids]
    selected = [dish for dish in selected if dish]
    if budget:
        running = 0
        limited = []
        for dish in selected:
            if running + dish["price"] <= budget or not limited:
                limited.append(dish)
                running += dish["price"]
        selected = limited

    total = sum(dish["price"] for dish in selected)
    return jsonify(
        {
            "reply": (
                "给你生成了一份餐品盲盒，适合不知道吃什么的时候直接试试。"
                if blind_box
                else f"根据你的需求，推荐这套搭配，预计 ￥{total}。"
            ),
            "items": [{"id": dish["id"], "quantity": 1} for dish in selected],
            "total": total,
        }
    )


@app.post("/api/ai/chat")
def ai_chat():
    if request.form or request.files:
        message = request.form.get("message", "").strip()
        image_file = request.files.get("image")
    else:
        data = request.get_json(silent=True) or {}
        message = data.get("message", "").strip()
        image_file = None

    if not message and not image_file:
        return jsonify({"message": "请输入你的点餐需求"}), 400

    api_key = os.environ.get("ZHIPU_API_KEY", "").strip()
    if not api_key:
        return jsonify({"message": "智谱 API Key 还没有配置，请先设置 ZHIPU_API_KEY。"}), 503

    menu_text = "\n".join(
        f"- {dish['name']}：{dish['category']}，￥{dish['price']}，{dish['description']}"
        for dish in menu_with_sales()
    )
    user_content = message or "请识别这张图片，并结合本店菜单给我点餐建议。"
    model = os.environ.get("ZHIPU_MODEL", "glm-4-flash")
    if image_file and image_file.filename:
        image_bytes = image_file.read()
        if len(image_bytes) > 4 * 1024 * 1024:
            return jsonify({"message": "图片太大了，请换一张 4MB 以内的图片。"}), 400
        image_ext = os.path.splitext(image_file.filename)[1].lower().lstrip(".") or "jpeg"
        if image_ext == "jpg":
            image_ext = "jpeg"
        image_data = base64.b64encode(image_bytes).decode("utf-8")
        user_content = [
            {"type": "text", "text": user_content},
            {"type": "image_url", "image_url": {"url": f"data:image/{image_ext};base64,{image_data}"}},
        ]
        model = os.environ.get("ZHIPU_VISION_MODEL", "glm-4.6v-flash")

    payload = {
        "model": model,
        "messages": [
            {
                "role": "system",
                "content": (
                    "你是雨石屋的 AI 点餐助手。你只围绕本店菜单推荐菜品，"
                    "需要根据用户的人数、预算、口味、忌口进行搭配，并给出总价估算。"
                    "回复要简洁、亲切，适合手机点餐页面展示。\n\n"
                    f"本店菜单：\n{menu_text}"
                ),
            },
            {"role": "user", "content": user_content},
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
    with get_db() as conn:
        cursor = conn.execute(
            "UPDATE orders SET status = ? WHERE id = ?",
            (status, order_id),
        )
        if cursor.rowcount:
            return jsonify(fetch_orders("WHERE id = ?", (order_id,))[0])

    return jsonify({"message": "订单不存在"}), 404


@app.delete("/api/orders/<int:order_id>")
@admin_required
def delete_order(order_id):
    with get_db() as conn:
        order = conn.execute("SELECT id FROM orders WHERE id = ?", (order_id,)).fetchone()
        if order is None:
            return jsonify({"message": "订单不存在"}), 404
        conn.execute("UPDATE orders SET admin_deleted = 1 WHERE id = ?", (order_id,))
    return jsonify({"message": "订单已从商家后台移除"})


@app.delete("/api/my/orders/<int:order_id>")
@login_required
def delete_my_order(order_id):
    user_id = session["user_id"]
    with get_db() as conn:
        order = conn.execute(
            "SELECT id FROM orders WHERE id = ? AND user_id = ?",
            (order_id, user_id),
        ).fetchone()
        if order is None:
            return jsonify({"message": "订单不存在"}), 404
        conn.execute("UPDATE orders SET customer_deleted = 1 WHERE id = ?", (order_id,))
    return jsonify({"message": "订单已从你的列表移除"})


@app.post("/api/my/orders/<int:order_id>/cancel")
@login_required
def cancel_my_order(order_id):
    user_id = session["user_id"]
    with get_db() as conn:
        order = conn.execute(
            "SELECT id, status FROM orders WHERE id = ? AND user_id = ?",
            (order_id, user_id),
        ).fetchone()
        if order is None:
            return jsonify({"message": "订单不存在"}), 404
        if order["status"] in {"已完成", "已取消"}:
            return jsonify({"message": "当前订单不能取消"}), 400
        conn.execute("UPDATE orders SET status = '已取消' WHERE id = ?", (order_id,))
        conn.execute(
            "UPDATE coupons SET status = 'unused', used_at = NULL, order_id = NULL WHERE order_id = ?",
            (order_id,),
        )
    return jsonify(fetch_orders("WHERE id = ?", (order_id,))[0])


init_db()


if __name__ == "__main__":
    port = int(os.environ.get("PORT", 5000))
    app.run(host="0.0.0.0", port=port, debug=False, use_reloader=False)
