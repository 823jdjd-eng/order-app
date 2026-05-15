import base64
from datetime import date, datetime, timedelta
import json
import os
import random
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


REAL_FOOD_IMAGES = [
    "https://images.unsplash.com/photo-1555126634-323283e090fa?auto=format&fit=crop&w=760&q=82",
    "https://images.unsplash.com/photo-1603133872878-684f208fb84b?auto=format&fit=crop&w=760&q=82",
    "https://images.unsplash.com/photo-1512058564366-18510be2db19?auto=format&fit=crop&w=760&q=82",
    "https://images.unsplash.com/photo-1563379091339-03246963d29a?auto=format&fit=crop&w=760&q=82",
    "https://images.unsplash.com/photo-1617093727343-374698b1b08d?auto=format&fit=crop&w=760&q=82",
    "https://images.unsplash.com/photo-1582878826629-29b7ad1cdc43?auto=format&fit=crop&w=760&q=82",
    "https://images.unsplash.com/photo-1559847844-5315695dadae?auto=format&fit=crop&w=760&q=82",
    "https://images.unsplash.com/photo-1546069901-d5bfd2cbfb1f?auto=format&fit=crop&w=760&q=82",
    "https://images.unsplash.com/photo-1546069901-ba9599a7e63c?auto=format&fit=crop&w=760&q=82",
    "https://images.unsplash.com/photo-1604908176997-125f25cc6f3d?auto=format&fit=crop&w=760&q=82",
    "https://images.unsplash.com/photo-1518977676601-b53f82aba655?auto=format&fit=crop&w=760&q=82",
    "https://images.unsplash.com/photo-1604909052743-94e838986d24?auto=format&fit=crop&w=760&q=82",
    "https://images.unsplash.com/photo-1544025162-d76694265947?auto=format&fit=crop&w=760&q=82",
    "https://images.unsplash.com/photo-1567620832903-9fc6debc209f?auto=format&fit=crop&w=760&q=82",
    "https://images.unsplash.com/photo-1605478371310-a9f1e96b4ff4?auto=format&fit=crop&w=760&q=82",
    "https://images.unsplash.com/photo-1625938144755-652e08e359b7?auto=format&fit=crop&w=760&q=82",
    "https://images.unsplash.com/photo-1612929633738-8fe44f7ec841?auto=format&fit=crop&w=760&q=82",
    "https://images.unsplash.com/photo-1455619452474-d2be8b1e70cd?auto=format&fit=crop&w=760&q=82",
    "https://images.unsplash.com/photo-1532550907401-a500c9a57435?auto=format&fit=crop&w=760&q=82",
    "https://images.unsplash.com/photo-1516684732162-798a0062be99?auto=format&fit=crop&w=760&q=82",
    "https://images.unsplash.com/photo-1496116218417-1a781b1c416c?auto=format&fit=crop&w=760&q=82",
    "https://images.unsplash.com/photo-1566385101042-1a0aa0c1268c?auto=format&fit=crop&w=760&q=82",
    "https://images.unsplash.com/photo-1582169296194-e4d644c48063?auto=format&fit=crop&w=760&q=82",
    "https://images.unsplash.com/photo-1600891964599-f61ba0e24092?auto=format&fit=crop&w=760&q=82",
]


def build_extended_menu():
    stews = [
        ("土豆炖豆角", 20, "土豆绵软，豆角入味，东北家常炖菜"),
        ("白菜炖豆腐", 10, "白菜清甜，豆腐嫩滑，汤汁鲜暖"),
        ("小鸡炖土豆", 30, "鸡肉鲜嫩，土豆吸满汤汁，适合配米饭"),
        ("排骨炖豆角", 36, "排骨酱香浓郁，豆角软烂入味"),
        ("牛腩炖土豆", 38, "牛腩软糯，土豆绵密，汤汁浓厚"),
        ("番茄炖牛腩", 39, "番茄酸甜，牛腩醇厚，暖胃开胃"),
        ("酸菜炖粉条", 18, "酸菜爽口，粉条滑弹，东北老味道"),
        ("猪肉炖粉条", 28, "五花肉香，粉条吸汁，热乎下饭"),
        ("豆角炖南瓜", 18, "南瓜清甜，豆角鲜嫩，口感柔和"),
        ("茄子炖土豆", 18, "茄子软糯，土豆吸汁，家常酱香"),
        ("鲫鱼炖豆腐", 32, "鱼汤鲜白，豆腐嫩滑，清鲜暖身"),
        ("冬瓜炖丸子", 24, "冬瓜清爽，肉丸弹嫩，汤头清亮"),
        ("蘑菇炖鸡", 34, "蘑菇鲜香，鸡肉软嫩，汤汁浓郁"),
        ("白菜炖粉条", 16, "白菜清甜，粉条滑顺，简单舒服"),
        ("萝卜炖牛肉", 36, "萝卜吸满肉香，牛肉软烂"),
        ("海带炖排骨", 32, "排骨鲜香，海带清爽，汤味厚实"),
        ("芸豆炖土豆", 19, "芸豆软烂，土豆绵密，酱香足"),
        ("豆腐炖鱼块", 34, "鱼块鲜嫩，豆腐吸汤，咸鲜适口"),
        ("鸡腿炖蘑菇", 33, "鸡腿肉厚，蘑菇鲜香，汤汁下饭"),
        ("牛肉炖萝卜", 37, "牛肉浓香，萝卜清甜解腻"),
        ("土豆炖排骨", 34, "排骨入味，土豆软糯，分量扎实"),
        ("豆角炖五花肉", 29, "五花肉焦香，豆角软烂"),
        ("羊肉炖萝卜", 42, "羊肉鲜香，萝卜清甜，冬日热乎"),
        ("番茄炖豆腐", 18, "番茄酸甜，豆腐嫩滑，清爽下饭"),
        ("酸菜炖白肉", 31, "酸菜解腻，白肉香嫩，东北风味"),
        ("茄子炖粉条", 19, "茄子软糯，粉条滑弹，酱香浓"),
        ("白菜炖丸子", 22, "白菜清甜，丸子鲜弹，汤汁舒服"),
        ("南瓜炖排骨", 33, "南瓜香甜，排骨咸鲜，层次丰富"),
        ("鸡块炖豆角", 31, "鸡块鲜嫩，豆角入味，家常大菜"),
        ("土豆炖牛肉", 37, "土豆绵软，牛肉醇香，汤汁浓厚"),
        ("腐竹炖排骨", 35, "腐竹吸汁，排骨软香，口感扎实"),
        ("豆腐炖白菜粉", 17, "豆腐白菜粉条，清鲜热乎"),
        ("酸菜炖冻豆腐", 20, "冻豆腐吸汤，酸菜爽脆"),
        ("黄豆炖猪蹄", 40, "猪蹄软糯，黄豆绵香，胶质满满"),
        ("玉米炖排骨", 34, "玉米清甜，排骨鲜香，汤汁温润"),
        ("莲藕炖排骨", 36, "莲藕粉糯，排骨醇香"),
        ("豆角炖宽粉", 18, "宽粉弹滑，豆角酱香，素食也满足"),
        ("小白菜炖豆腐", 15, "小白菜鲜嫩，豆腐清香"),
        ("蘑菇炖豆腐", 18, "菌香浓郁，豆腐嫩滑"),
        ("鸡翅炖土豆", 32, "鸡翅软嫩，土豆吸汁"),
        ("牛筋炖萝卜", 43, "牛筋软糯，萝卜清甜"),
        ("番茄土豆炖牛肉", 39, "酸甜浓郁，肉香饱满"),
        ("豆角炖排骨粉条", 38, "排骨豆角粉条，一锅香浓"),
        ("白菜炖虾仁豆腐", 28, "虾仁鲜甜，豆腐白菜清爽"),
        ("酸菜炖鸡块", 30, "酸菜开胃，鸡块鲜嫩"),
        ("香菇炖土鸡", 42, "香菇浓香，土鸡肉质紧实"),
        ("萝卜炖羊排", 45, "羊排鲜香，萝卜清甜"),
        ("豆腐炖肉末", 19, "肉末咸香，豆腐滑嫩"),
        ("土豆炖茄子", 17, "土豆茄子双软糯，酱香浓"),
        ("白菜炖海带", 15, "白菜清甜，海带鲜爽，轻盈热乎"),
    ]
    stir_fries = [
        ("炒干豆腐", 15, "干豆腐软韧入味，大火快炒更香"),
        ("豆腐炒鸡蛋", 13, "豆腐细嫩，鸡蛋香软，口味清爽"),
        ("韭菜炒鸡蛋", 15, "韭菜鲜香，鸡蛋蓬松，现炒上桌"),
        ("土豆丝炒鸡蛋", 13, "土豆丝爽口，鸡蛋香软，家常味十足"),
        ("蒜苔炒肉", 18, "蒜苔脆香，肉片鲜嫩，米饭好搭档"),
        ("尖椒干豆腐", 16, "尖椒清香，干豆腐软韧，东北经典"),
        ("木耳炒鸡蛋", 15, "木耳脆爽，鸡蛋香嫩"),
        ("鱼香肉丝", 24, "酸甜微辣，肉丝滑嫩，开胃下饭"),
        ("宫保鸡丁", 26, "鸡丁鲜嫩，花生香脆，甜辣均衡"),
        ("青椒肉丝", 20, "青椒清香，肉丝滑嫩，锅气十足"),
        ("西红柿炒鸡蛋", 14, "酸甜番茄，滑嫩鸡蛋，家常经典"),
        ("地三鲜", 18, "茄子土豆青椒，软糯咸香"),
        ("干煸豆角", 18, "豆角焦香，干香入味"),
        ("蒜蓉生菜", 13, "生菜清脆，蒜香鲜亮"),
        ("手撕包菜", 14, "包菜脆甜，干椒炝香"),
        ("麻婆豆腐", 16, "豆腐嫩滑，麻辣鲜香"),
        ("孜然羊肉", 34, "羊肉焦香，孜然味足"),
        ("葱爆牛肉", 32, "牛肉鲜嫩，葱香浓郁"),
        ("香菇滑鸡", 26, "香菇浓郁，鸡肉滑嫩"),
        ("辣椒炒肉", 22, "辣椒香辣，肉片鲜嫩，下饭有劲"),
        ("蒜黄炒鸡蛋", 16, "蒜黄清香，鸡蛋软嫩"),
        ("芹菜炒肉", 19, "芹菜清脆，肉片咸香"),
        ("莲藕炒肉片", 21, "莲藕脆甜，肉片鲜香"),
        ("黄瓜炒鸡蛋", 13, "黄瓜清爽，鸡蛋嫩香"),
        ("西兰花炒虾仁", 30, "虾仁弹嫩，西兰花清爽"),
        ("荷兰豆炒腊肠", 26, "荷兰豆清甜，腊肠浓香"),
        ("香辣鸡翅", 28, "鸡翅焦香，微辣入味"),
        ("回锅肉", 26, "五花肉焦香，蒜苗提味"),
        ("京酱肉丝", 25, "肉丝酱香，咸甜适口"),
        ("锅包肉", 30, "外酥里嫩，酸甜东北味"),
        ("糖醋里脊", 28, "里脊酥嫩，酸甜开胃"),
        ("酱爆鸡丁", 24, "鸡丁滑嫩，酱香浓郁"),
        ("韭菜炒豆芽", 13, "豆芽脆嫩，韭香清爽"),
        ("大葱炒鸡蛋", 14, "葱香浓，鸡蛋软嫩"),
        ("素炒三丝", 12, "三丝清爽，轻盈下饭"),
        ("清炒油麦菜", 13, "油麦菜清脆，蒜香柔和"),
        ("香辣土豆片", 15, "土豆片焦香，香辣适口"),
        ("肉末茄子", 20, "茄子软糯，肉末咸香"),
        ("豆角炒肉", 20, "豆角爽脆，肉片鲜嫩"),
        ("尖椒炒鸡蛋", 14, "尖椒清香，鸡蛋蓬松"),
        ("酸辣白菜", 12, "白菜爽脆，酸辣开胃"),
        ("蒜香排骨", 32, "排骨焦香，蒜香浓郁"),
        ("蚝油生菜", 13, "生菜清甜，蚝油鲜香"),
        ("香干炒肉", 19, "香干韧香，肉片鲜嫩"),
        ("木须肉", 22, "鸡蛋木耳肉片，家常均衡"),
        ("白菜炒粉条", 15, "白菜清甜，粉条滑弹"),
        ("香辣虾", 38, "虾肉鲜弹，香辣浓郁"),
        ("黑椒牛柳", 36, "牛柳嫩滑，黑椒香气足"),
        ("炒合菜", 16, "多种时蔬快炒，清爽有锅气"),
        ("葱姜炒鸡块", 28, "鸡块鲜嫩，葱姜香浓"),
    ]
    menu = []
    for index, (name, price, description) in enumerate(stews, start=1):
        options = [{"id": "fentiao", "name": "加粉条", "price": 5}]
        if any(key in name for key in ["排骨", "牛", "羊", "猪蹄", "鸡"]):
            options.append({"id": "tuodou", "name": "加土豆", "price": 4})
        menu.append({
            "id": index,
            "name": name,
            "category": "现做炖菜",
            "price": price,
            "tag": "现炖热乎",
            "sales": 0,
            "description": description,
            "image": REAL_FOOD_IMAGES[(index - 1) % len(REAL_FOOD_IMAGES)],
            "options": options,
        })
    for offset, (name, price, description) in enumerate(stir_fries, start=1):
        dish_id = 50 + offset
        options = []
        if any(key in name for key in ["豆腐", "鸡蛋", "土豆丝", "豆角", "白菜", "生菜", "包菜", "油麦菜", "合菜"]):
            options.append({"id": "rouding", "name": "加肉丁", "price": 5})
        menu.append({
            "id": dish_id,
            "name": name,
            "category": "精品炒菜",
            "price": price,
            "tag": "现炒锅气",
            "sales": 0,
            "description": description,
            "image": REAL_FOOD_IMAGES[(dish_id - 1) % len(REAL_FOOD_IMAGES)],
            "options": options,
        })
    menu.extend([
        {"id": 201, "name": "现焖米饭", "category": "主食", "price": 3, "tag": "现焖", "sales": 0, "description": "一人份现焖米饭，颗粒饱满", "image": "https://images.unsplash.com/photo-1536304993881-ff6e9eefa2a6?auto=format&fit=crop&w=760&q=82", "options": []},
        {"id": 202, "name": "烀饼", "category": "主食", "price": 10, "tag": "炖菜限定", "sales": 0, "description": "炖菜点单推荐搭配，吸汤更香", "image": "https://images.unsplash.com/photo-1578985545062-69928b1d9587?auto=format&fit=crop&w=760&q=82", "options": []},
        {"id": 301, "name": "可口可乐", "category": "饮品", "price": 4, "tag": "冰爽", "sales": 0, "description": "经典汽水，冰镇更爽", "image": "https://images.unsplash.com/photo-1622483767028-3f66f32aef97?auto=format&fit=crop&w=760&q=82", "options": []},
        {"id": 302, "name": "芬达", "category": "饮品", "price": 4, "tag": "橙味", "sales": 0, "description": "橙味汽水，甜爽解腻", "image": "https://images.unsplash.com/photo-1621506289937-a8e4df240d0b?auto=format&fit=crop&w=760&q=82", "options": []},
        {"id": 303, "name": "雪碧", "category": "饮品", "price": 4, "tag": "清爽", "sales": 0, "description": "柠檬味汽水，清爽提神", "image": "https://images.unsplash.com/photo-1544145945-f90425340c7e?auto=format&fit=crop&w=760&q=82", "options": []},
        {"id": 304, "name": "大窑", "category": "饮品", "price": 7, "tag": "大瓶", "sales": 0, "description": "东北餐桌经典汽水，分量更足", "image": "https://images.unsplash.com/photo-1513558161293-cdaf765ed2fd?auto=format&fit=crop&w=760&q=82", "options": []},
        {"id": 305, "name": "美年达", "category": "饮品", "price": 4, "tag": "果味", "sales": 0, "description": "果味汽水，适合搭配热菜", "image": "https://images.unsplash.com/photo-1621506289937-a8e4df240d0b?auto=format&fit=crop&w=760&q=82", "options": []},
    ])
    return menu


def build_luxury_menu():
    def romantic_image(topic, seed):
        return "/static/uploads/dishes/dish-{:02d}.png".format(seed)

    dishes = [
        (1, "惠灵顿牛排双人份", "主厨西餐", 188, "招牌", "酥皮包裹菲力牛排，蘑菇酱馅浓郁，适合仪式感晚餐", romantic_image("beef wellington", 1)),
        (2, "黑松露奶油意面", "主厨西餐", 78, "人气", "帕玛森奶香、黑松露香气和手工意面交织", romantic_image("truffle cream pasta", 2)),
        (3, "香煎三文鱼配柠檬黄油", "主厨西餐", 96, "轻奢", "外皮微脆，鱼肉细嫩，配柠檬黄油汁", romantic_image("salmon lemon butter", 3)),
        (4, "法式鹅肝焦糖苹果", "主厨西餐", 128, "限定", "鹅肝绵密丰润，焦糖苹果带来清甜层次", romantic_image("foie gras apple", 4)),
        (5, "波士顿龙虾意面", "主厨西餐", 168, "海鲜", "龙虾肉弹嫩，番茄白葡萄酒酱汁鲜甜", romantic_image("lobster pasta", 5)),
        (6, "红酒慢炖牛脸颊", "主厨西餐", 138, "慢炖", "牛脸颊软糯入味，红酒酱汁醇厚", romantic_image("red wine beef", 6)),
        (7, "香草羊排配迷迭香汁", "主厨西餐", 158, "精选", "羊排焦香多汁，迷迭香和黑胡椒收尾", romantic_image("lamb chop rosemary", 7)),
        (8, "奶油蘑菇烩鸡", "主厨西餐", 88, "温柔", "鸡腿肉鲜嫩，奶油蘑菇汁柔和浓郁", romantic_image("cream mushroom chicken", 8)),
        (9, "玫瑰番茄布拉塔沙拉", "前菜沙拉", 58, "清爽", "布拉塔奶香丰盈，番茄酸甜，玫瑰盐提味", romantic_image("burrata tomato salad", 9)),
        (10, "生蚝三枚配香槟醋汁", "前菜沙拉", 99, "浪漫", "冰镇生蚝清甜，香槟醋汁轻盈开胃", romantic_image("oysters champagne", 10)),
        (11, "凯撒沙拉配帕玛森脆片", "前菜沙拉", 48, "经典", "罗马生菜爽脆，帕玛森咸香，酱汁细腻", romantic_image("caesar salad parmesan", 11)),
        (12, "烟熏三文鱼牛油果塔", "前菜沙拉", 72, "精致", "烟熏鱼香与牛油果绵密口感平衡", romantic_image("smoked salmon avocado", 12)),
        (13, "松露薯条配蒜香蛋黄酱", "前菜沙拉", 42, "小食", "现炸薯条、松露油和蒜香蛋黄酱", romantic_image("truffle fries", 13)),
        (14, "芝士火腿拼盘", "前菜沙拉", 118, "分享", "进口芝士、风干火腿、坚果与果干", romantic_image("cheese ham board", 14)),
        (15, "香煎扇贝柚子沙拉", "前菜沙拉", 76, "轻盈", "扇贝焦香，柚子油醋汁带来清爽果香", romantic_image("scallop salad", 15)),
        (16, "蜜桃火腿芝麻菜", "前菜沙拉", 66, "果香", "蜜桃清甜、火腿咸香，芝麻菜微苦平衡", romantic_image("peach prosciutto arugula", 16)),
        (17, "松露奶油烩饭", "浪漫主食", 68, "醇香", "意式烩饭米、松露奶油和帕玛森芝士", romantic_image("truffle risotto", 17)),
        (18, "番茄罗勒海鲜意面", "浪漫主食", 86, "鲜甜", "虾仁、贝柱、番茄罗勒酱和白葡萄酒香", romantic_image("seafood pasta tomato basil", 18)),
        (19, "牛肝菌蘑菇烩饭", "浪漫主食", 72, "菌香", "牛肝菌、蘑菇和奶油慢慢收汁", romantic_image("porcini mushroom risotto", 19)),
        (20, "香煎鸡胸藜麦碗", "浪漫主食", 62, "轻食", "鸡胸、藜麦、牛油果和清爽油醋汁", romantic_image("chicken quinoa bowl", 20)),
        (21, "龙虾汤配蒜香面包", "浪漫主食", 88, "浓汤", "龙虾壳熬汤底，入口浓郁鲜香", romantic_image("lobster bisque bread", 21)),
        (22, "南瓜鼠尾草手工饺", "浪漫主食", 69, "手作", "南瓜甜香、黄油鼠尾草和薄皮手工饺", romantic_image("pumpkin ravioli sage", 22)),
        (23, "海胆奶油天使面", "浪漫主食", 118, "海味", "海胆鲜甜与奶油轻裹细面，余味温柔", romantic_image("sea urchin angel hair pasta", 23)),
        (24, "黑椒牛柳焗饭", "浪漫主食", 79, "暖胃", "牛柳嫩滑，黑椒酱浓郁，芝士焗至微焦", romantic_image("beef baked rice", 24)),
        (25, "玫瑰盐烤春鸡", "臻选主菜", 118, "香烤", "春鸡外皮焦香，玫瑰盐和香草提亮肉汁", romantic_image("roast chicken herbs", 25)),
        (26, "安格斯肋眼配黑椒汁", "臻选主菜", 198, "厚切", "肋眼油花丰盈，黑椒汁醇厚收尾", romantic_image("ribeye steak sauce", 26)),
        (27, "蜂蜜芥末慢烤肋排", "臻选主菜", 128, "浓香", "猪肋排软嫩脱骨，蜂蜜芥末甜咸交错", romantic_image("pork ribs honey", 27)),
        (28, "香草黄油烤鳕鱼", "臻选主菜", 116, "细嫩", "鳕鱼肉洁白细嫩，香草黄油温润包裹", romantic_image("cod herb butter", 28)),
        (29, "蒜香黄油大虾", "臻选主菜", 98, "海鲜", "大虾弹嫩，蒜香黄油和柠檬汁清亮开胃", romantic_image("garlic butter shrimp", 29)),
        (30, "玫瑰烟熏鸭胸", "臻选主菜", 108, "微甜", "鸭胸油脂丰盈，烟熏香和莓果汁平衡", romantic_image("smoked duck breast", 30)),
        (31, "迷迭香羊小排", "臻选主菜", 168, "精选", "羊小排焦香多汁，迷迭香气息干净悠长", romantic_image("rosemary lamb rack", 31)),
        (32, "焦化洋葱牛肉排", "臻选主菜", 76, "治愈", "手打牛肉排配焦化洋葱，肉汁饱满", romantic_image("hamburger steak onion", 32)),
        (33, "法式洋葱汤", "暖心汤品", 48, "经典", "洋葱慢炒出甜味，芝士面包烤至金黄", romantic_image("french onion soup", 33)),
        (34, "奶油南瓜浓汤", "暖心汤品", 39, "温柔", "南瓜细腻绵密，奶油和坚果香气轻盈", romantic_image("pumpkin cream soup", 34)),
        (35, "松茸鸡汤盅", "暖心汤品", 68, "滋养", "松茸清香、鸡汤澄澈，适合慢慢暖胃", romantic_image("matsutake chicken soup", 35)),
        (36, "番茄牛尾汤", "暖心汤品", 72, "浓郁", "牛尾慢炖软糯，番茄酸甜让汤底更明亮", romantic_image("oxtail tomato soup", 36)),
        (37, "海鲜巧达浓汤", "暖心汤品", 58, "鲜甜", "蛤蜊、虾仁和奶油汤底，入口饱满", romantic_image("seafood chowder", 37)),
        (38, "菌菇清汤配脆片", "暖心汤品", 42, "清雅", "多种菌菇熬出清甜，配帕玛森脆片", romantic_image("mushroom clear soup", 38)),
        (39, "龙虾番茄清汤", "暖心汤品", 88, "轻奢", "龙虾壳熬制汤底，番茄让鲜味更通透", romantic_image("lobster tomato soup", 39)),
        (40, "白葡萄酒蛤蜊汤", "暖心汤品", 56, "微醺", "蛤蜊鲜甜，白葡萄酒香气轻盈", romantic_image("clam white wine soup", 40)),
        (41, "海盐焦糖提拉米苏", "甜品", 46, "甜蜜", "咖啡酒香、马斯卡彭奶油和海盐焦糖", romantic_image("tiramisu caramel", 41)),
        (42, "覆盆子熔岩巧克力", "甜品", 52, "心动", "热巧克力流心配覆盆子酸甜果香", romantic_image("raspberry lava cake", 42)),
        (43, "玫瑰荔枝慕斯", "甜品", 49, "七夕", "玫瑰花香、荔枝果香与轻盈慕斯", romantic_image("rose lychee mousse", 43)),
        (44, "香草焦糖布蕾", "甜品", 39, "法式", "焦糖脆壳下是细腻香草蛋奶", romantic_image("creme brulee vanilla", 44)),
        (45, "草莓拿破仑", "甜品", 56, "限定", "酥皮、草莓和卡仕达奶油层层叠起", romantic_image("strawberry mille feuille", 45)),
        (46, "双人甜品礼盒", "甜品", 98, "双人", "四款迷你甜点组合，适合饭后分享", romantic_image("dessert box for two", 46)),
        (47, "抹茶白巧芝士蛋糕", "甜品", 45, "清新", "抹茶微苦、白巧柔甜，芝士口感绵密", romantic_image("matcha cheesecake", 47)),
        (48, "樱桃黑森林杯", "甜品", 42, "复古", "樱桃酒香、可可蛋糕和奶油层次分明", romantic_image("black forest dessert cup", 48)),
        (49, "松露薯泥", "精致小食", 36, "绵密", "土豆泥细腻，松露香气和黄油香缓慢展开", romantic_image("truffle mashed potato", 49)),
        (50, "蒜香烤口蘑", "精致小食", 32, "多汁", "口蘑烤出汁水，蒜香黄油入口浓郁", romantic_image("garlic mushroom appetizer", 50)),
        (51, "帕玛森炸鸡块", "精致小食", 46, "酥脆", "鸡块外酥里嫩，帕玛森咸香更有层次", romantic_image("parmesan fried chicken", 51)),
        (52, "迷你牛肉塔可", "精致小食", 42, "分享", "牛肉酱香浓郁，酸奶油和莎莎酱清爽", romantic_image("mini beef taco", 52)),
        (53, "香煎芝士年糕", "精致小食", 34, "拉丝", "年糕外壳微脆，芝士柔软拉丝", romantic_image("cheese rice cake", 53)),
        (54, "黄油玉米杯", "精致小食", 28, "香甜", "甜玉米、黄油和海盐，简单但很讨喜", romantic_image("butter corn cup", 54)),
        (55, "罗勒番茄烤面包", "精致小食", 38, "清爽", "烤面包酥脆，番茄罗勒鲜亮开胃", romantic_image("tomato basil bruschetta", 55)),
        (56, "蜂蜜坚果烤芝士", "精致小食", 58, "微甜", "烤芝士温热流心，蜂蜜和坚果增加香气", romantic_image("baked cheese honey nuts", 56)),
        (57, "玫瑰可乐特调", "酒水饮品", 28, "特调", "可口可乐、玫瑰糖浆和柠檬片，保留可乐券适用", romantic_image("rose cola mocktail", 57)),
        (58, "赤霞珠红酒杯", "酒水饮品", 68, "红酒", "黑莓果香、单宁柔顺，适合搭配牛排", romantic_image("cabernet wine glass", 58)),
        (59, "粉桃香槟气泡", "酒水饮品", 58, "微醺", "粉桃香气和细腻气泡，适合约会开场", romantic_image("peach champagne", 59)),
        (60, "无酒精玫瑰气泡水", "酒水饮品", 32, "无酒精", "玫瑰、荔枝和苏打气泡，清甜不腻", romantic_image("rose sparkling water", 60)),
        (61, "手冲耶加雪菲", "酒水饮品", 36, "咖啡", "花果香明显，适合饭后慢慢聊", romantic_image("pour over coffee", 61)),
        (62, "烛光热红酒", "酒水饮品", 48, "热饮", "红酒、橙皮、肉桂与丁香慢煮", romantic_image("mulled wine candlelight", 62)),
        (63, "荔枝白茶冷萃", "酒水饮品", 29, "茶饮", "白茶清香叠加荔枝果甜，清透解腻", romantic_image("lychee white tea", 63)),
        (64, "莓果莫吉托", "酒水饮品", 42, "清爽", "莓果酸甜、薄荷清凉，气泡感轻快", romantic_image("berry mojito", 64)),
        (65, "海盐焦糖拿铁", "酒水饮品", 34, "咖啡", "焦糖甜香和海盐收尾，奶泡细腻", romantic_image("sea salt caramel latte", 65)),
        (66, "桂花乌龙奶盖", "酒水饮品", 31, "奶盖", "乌龙茶香、桂花清甜和轻盈奶盖", romantic_image("osmanthus oolong milk foam", 66)),
    ]
    return [
        {
            "id": dish_id,
            "name": name,
            "category": category,
            "price": price,
            "tag": tag,
            "sales": 0,
            "description": description,
            "image": image,
            "options": [],
        }
        for dish_id, name, category, price, tag, description, image in dishes
    ]


MENU = build_luxury_menu()
CATEGORY_ORDER = ["主厨西餐", "前菜沙拉", "浪漫主食", "臻选主菜", "暖心汤品", "甜品", "精致小食", "酒水饮品"]
WHEEL_MEAL_DISH_IDS = [
    dish["id"] for dish in MENU
    if dish["price"] <= 88 and dish["category"] in ("主厨西餐", "浪漫主食", "臻选主菜", "甜品", "精致小食")
][:5]


def menu_item(dish_id):
    return next((dish for dish in MENU if dish["id"] == int(dish_id)), None)


def wheel_meal_dishes():
    return [dish for dish in (menu_item(dish_id) for dish_id in WHEEL_MEAL_DISH_IDS) if dish]


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
        ensure_column(conn, "users", "balance", "REAL NOT NULL DEFAULT 0")
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
        ensure_column(conn, "coupons", "target_type", "TEXT NOT NULL DEFAULT 'order'")
        ensure_column(conn, "coupons", "target_dish_id", "INTEGER")
        ensure_column(conn, "coupons", "discount_type", "TEXT NOT NULL DEFAULT 'amount'")
        ensure_column(conn, "coupons", "discount_rate", "REAL")
        conn.execute(
            """
            UPDATE coupons
            SET target_type = 'dish', target_dish_id = 301, min_amount = 0, discount_type = 'amount'
            WHERE title LIKE '%可乐%' AND status = 'unused'
            """
        )
        conn.execute(
            """
            UPDATE coupons
            SET target_type = 'any_dish', target_dish_id = NULL, amount = 0, min_amount = 0,
                discount_type = 'rate', discount_rate = 0.5
            WHERE title LIKE '%五折%' AND status = 'unused'
            """
        )
        for dish in MENU:
            conn.execute(
                """
                UPDATE coupons
                SET target_type = 'dish', target_dish_id = ?, amount = ?, min_amount = 0, discount_type = 'amount'
                WHERE title = ? AND status = 'unused'
                """,
                (dish["id"], dish["price"], "{}免费餐券".format(dish["name"])),
            )
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
        conn.execute(
            """
            CREATE TABLE IF NOT EXISTS balance_transactions (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                user_id INTEGER NOT NULL,
                amount REAL NOT NULL,
                kind TEXT NOT NULL,
                note TEXT,
                created_at TEXT NOT NULL,
                FOREIGN KEY(user_id) REFERENCES users(id)
            )
            """
        )
        conn.execute(
            """
            CREATE TABLE IF NOT EXISTS withdrawals (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                user_id INTEGER NOT NULL,
                wechat TEXT NOT NULL,
                amount REAL NOT NULL,
                status TEXT NOT NULL DEFAULT '已提交',
                created_at TEXT NOT NULL,
                FOREIGN KEY(user_id) REFERENCES users(id)
            )
            """
        )
        conn.execute(
            """
            CREATE TABLE IF NOT EXISTS wheel_records (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                user_id INTEGER NOT NULL,
                prize_type TEXT NOT NULL,
                title TEXT NOT NULL,
                created_at TEXT NOT NULL,
                FOREIGN KEY(user_id) REFERENCES users(id)
            )
            """
        )
        conn.execute(
            """
            CREATE TABLE IF NOT EXISTS complaints (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                user_id INTEGER NOT NULL,
                body TEXT NOT NULL,
                reply TEXT,
                status TEXT NOT NULL DEFAULT '待回复',
                created_at TEXT NOT NULL,
                replied_at TEXT,
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
            "SELECT id, username, nickname, avatar_url, role, points, balance, checkin_streak, last_checkin_date FROM users WHERE id = ?",
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
        "balance": user["balance"] if "balance" in user.keys() else 0,
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
        "target_type": row["target_type"] if "target_type" in row.keys() else "order",
        "target_dish_id": row["target_dish_id"] if "target_dish_id" in row.keys() else None,
        "discount_type": row["discount_type"] if "discount_type" in row.keys() else "amount",
        "discount_rate": row["discount_rate"] if "discount_rate" in row.keys() else None,
        "created_at": row["created_at"],
        "used_at": row["used_at"],
        "order_id": row["order_id"],
    }


def normalize_cart_items(raw_items):
    items = []
    menu_by_id = {dish["id"]: dish for dish in MENU}
    for item in raw_items or []:
        try:
            dish_id = int(item.get("id"))
            quantity = int(item.get("quantity", 0))
        except (TypeError, ValueError):
            continue
        dish = menu_by_id.get(dish_id)
        if dish is None or quantity <= 0:
            continue
        try:
            display_price = float(item.get("price", dish["price"]))
        except (TypeError, ValueError):
            display_price = float(dish["price"])
        items.append({"id": dish_id, "quantity": quantity, "price": display_price, "dish": dish})
    return items


def coupon_discount(row, cart_items):
    if row is None or row["status"] != "unused":
        return 0
    target_type = row["target_type"] if "target_type" in row.keys() and row["target_type"] else "order"
    discount_type = row["discount_type"] if "discount_type" in row.keys() and row["discount_type"] else "amount"
    amount = float(row["amount"] or 0)
    min_amount = float(row["min_amount"] or 0)
    subtotal = sum(item["price"] * item["quantity"] for item in cart_items)
    if subtotal <= 0:
        return 0

    if target_type == "dish":
        target_id = row["target_dish_id"] if "target_dish_id" in row.keys() else None
        target_total = sum(item["price"] * item["quantity"] for item in cart_items if item["id"] == target_id)
        if target_total <= 0 or target_total < min_amount:
            return 0
        return round(min(amount, target_total), 2)

    if target_type == "any_dish" or discount_type == "rate":
        eligible = [item["price"] for item in cart_items if item["quantity"] > 0]
        if not eligible or subtotal < min_amount:
            return 0
        rate = row["discount_rate"] if "discount_rate" in row.keys() and row["discount_rate"] else 0.5
        return round(max(eligible) * (1 - float(rate)), 2)

    if subtotal < min_amount:
        return 0
    return round(min(amount, subtotal), 2)


def coupon_label(coupon):
    target_type = coupon.get("target_type", "order")
    discount_type = coupon.get("discount_type", "amount")
    if target_type == "dish" and coupon.get("target_dish_id"):
        dish = menu_item(coupon["target_dish_id"])
        target = dish["name"] if dish else "指定商品"
        return "{}：仅限{}使用".format(coupon["title"], target)
    if target_type == "any_dish" or discount_type == "rate":
        return "{}：任意单品五折".format(coupon["title"])
    return "{}：满￥{}减￥{}".format(coupon["title"], coupon["min_amount"], coupon["amount"])


def serialize_message(row):
    return {
        "id": row["id"],
        "user_id": row["user_id"],
        "sender": row["sender"],
        "body": row["body"],
        "created_at": row["created_at"],
    }


def serialize_complaint(row):
    return {
        "id": row["id"],
        "user_id": row["user_id"],
        "username": row["username"] if "username" in row.keys() else "",
        "nickname": row["nickname"] if "nickname" in row.keys() else "",
        "body": row["body"],
        "reply": row["reply"] or "",
        "status": row["status"],
        "created_at": row["created_at"],
        "replied_at": row["replied_at"] or "",
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
    return render_template(
        "index.html",
        menu=menu,
        categories=categories,
        user=current_user(),
        wheel_slots=wheel_meal_dishes(),
        wheel_coke=menu_item(57),
    )


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
    packing_fee = 2
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
            discount = coupon_discount(coupon_row, order_items)
            if discount <= 0:
                return jsonify({"message": "优惠券不适用于当前商品"}), 400

        payable = max(float(total) + packing_fee - float(discount), 0)
        user_balance = conn.execute(
            "SELECT balance FROM users WHERE id = ?",
            (user_id,),
        ).fetchone()["balance"]
        if float(user_balance or 0) < payable:
            return jsonify(
                {
                    "message": "余额不足，请联系商家充值后再支付",
                    "balance": round(float(user_balance or 0), 2),
                    "payable": round(payable, 2),
                }
            ), 400

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
        conn.execute("UPDATE users SET balance = balance - ? WHERE id = ?", (payable, user_id))
        conn.execute(
            "INSERT INTO balance_transactions (user_id, amount, kind, note, created_at) VALUES (?, ?, 'pay', ?, ?)",
            (user_id, -payable, "订单 #{} 支付".format(order_id), now),
        )
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
    try:
        cart_items = normalize_cart_items(json.loads(request.args.get("items", "[]") or "[]"))
    except (TypeError, ValueError):
        cart_items = []
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
    row_by_id = {row["id"]: row for row in rows}
    fallback_items = [{"id": 0, "quantity": 1, "price": min_total, "dish": {}}] if min_total else []
    for coupon in coupons:
        discount = coupon_discount(row_by_id[coupon["id"]], cart_items or fallback_items)
        coupon["discount"] = discount
        coupon["available"] = coupon["status"] == "unused" and discount > 0
        coupon["label"] = coupon_label(coupon)
    return jsonify(coupons)


@app.delete("/api/my/coupons/<int:coupon_id>")
@login_required
def delete_my_coupon(coupon_id):
    with get_db() as conn:
        row = conn.execute(
            "SELECT id FROM coupons WHERE id = ? AND user_id = ?",
            (coupon_id, session["user_id"]),
        ).fetchone()
        if row is None:
            return jsonify({"message": "优惠券不存在"}), 404
        conn.execute("DELETE FROM coupons WHERE id = ? AND user_id = ?", (coupon_id, session["user_id"]))
    return jsonify({"message": "已删除"})


@app.get("/api/my/wallet")
@login_required
def my_wallet():
    user_id = session["user_id"]
    today_text = date.today().isoformat()
    with get_db() as conn:
        user = conn.execute(
            "SELECT points, balance, checkin_streak, last_checkin_date FROM users WHERE id = ?",
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
        wheel_records = conn.execute(
            """
            SELECT id, prize_type, title, created_at
            FROM wheel_records
            WHERE user_id = ?
            ORDER BY id DESC
            LIMIT 8
            """,
            (user_id,),
        ).fetchall()
        withdrawals = conn.execute(
            """
            SELECT id, wechat, amount, status, created_at
            FROM withdrawals
            WHERE user_id = ?
            ORDER BY id DESC
            LIMIT 5
            """,
            (user_id,),
        ).fetchall()
        transactions = conn.execute(
            """
            SELECT id, amount, kind, note, created_at
            FROM balance_transactions
            WHERE user_id = ?
            ORDER BY id DESC
            LIMIT 8
            """,
            (user_id,),
        ).fetchall()
    checked_today = user["last_checkin_date"] == today_text
    next_streak = user["checkin_streak"] if checked_today else user["checkin_streak"] + 1
    if user["last_checkin_date"]:
        last_day = parse_iso_date(user["last_checkin_date"])
        if not checked_today and last_day != date.today() - timedelta(days=1):
            next_streak = 1
    serialized_coupons = [serialize_coupon(row) for row in coupons]
    for coupon in serialized_coupons:
        coupon["label"] = coupon_label(coupon)
    return jsonify(
        {
            "points": user["points"],
            "balance": round(float(user["balance"] or 0), 2),
            "nickname": current_user()["nickname"] or current_user()["username"],
            "avatar_url": current_user()["avatar_url"] or "",
            "checkin_streak": user["checkin_streak"],
            "last_checkin_date": user["last_checkin_date"],
            "checked_today": checked_today,
            "next_reward": 0 if checked_today else reward_for_streak(next_streak),
            "coupons": serialized_coupons,
            "withdrawals": [dict(row) for row in withdrawals],
            "transactions": [dict(row) for row in transactions],
            "wheel_records": [dict(row) for row in wheel_records],
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


@app.post("/api/my/withdraw")
@login_required
def withdraw_balance():
    data = request.get_json(silent=True) or {}
    wechat = data.get("wechat", "").strip()
    try:
        amount = round(float(data.get("amount", 0) or 0), 2)
    except (TypeError, ValueError):
        amount = 0
    if not wechat:
        return jsonify({"message": "请填写微信号"}), 400
    if amount <= 0:
        return jsonify({"message": "提现金额必须大于 0"}), 400
    user_id = session["user_id"]
    now = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    with get_db() as conn:
        user = conn.execute("SELECT balance FROM users WHERE id = ?", (user_id,)).fetchone()
        balance = float(user["balance"] or 0)
        if balance < amount:
            return jsonify({"message": "余额不足，无法提现"}), 400
        conn.execute("UPDATE users SET balance = balance - ? WHERE id = ?", (amount, user_id))
        conn.execute(
            "INSERT INTO withdrawals (user_id, wechat, amount, status, created_at) VALUES (?, ?, ?, '已提交', ?)",
            (user_id, wechat, amount, now),
        )
        conn.execute(
            "INSERT INTO balance_transactions (user_id, amount, kind, note, created_at) VALUES (?, ?, 'withdraw', ?, ?)",
            (user_id, -amount, "微信提现申请", now),
        )
        balance = conn.execute("SELECT balance FROM users WHERE id = ?", (user_id,)).fetchone()["balance"]
    return jsonify({"message": "提现成功，预计24小时内到账", "balance": round(float(balance or 0), 2)})


@app.post("/api/my/wheel/spin")
@login_required
def spin_wheel():
    user_id = session["user_id"]
    cost = 9.9
    now = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    meal_pool = wheel_meal_dishes()
    roll = random.uniform(0, 100)
    if roll < 10:
        prize = {"type": "coupon", "title": "20元无门槛优惠券", "amount": 20, "min_amount": 0, "slot": 0, "target_type": "order", "discount_type": "amount"}
    elif roll < 15:
        prize = {"type": "balance", "title": "100元余额", "amount": 100, "slot": 1}
    elif roll < 65 and meal_pool:
        index = min(int((roll - 15) // 10), len(meal_pool) - 1)
        dish = meal_pool[index]
        prize = {"type": "meal", "title": "{}免费餐券".format(dish["name"]), "dish": dish, "slot": 2 + index}
    elif roll < 70:
        prize = {"type": "coupon", "title": "任意菜品五折餐券", "amount": 0, "min_amount": 0, "slot": 7, "target_type": "any_dish", "discount_type": "rate", "discount_rate": 0.5}
    elif roll < 80:
        coke = menu_item(57)
        prize = {"type": "coupon", "title": "玫瑰可乐特调兑换券", "amount": float(coke["price"] if coke else 28), "min_amount": 0, "slot": 8, "target_type": "dish", "target_dish_id": 57, "discount_type": "amount"}
    else:
        prize = {"type": "empty", "title": "谢谢参与", "slot": 9}
    with get_db() as conn:
        user = conn.execute("SELECT balance FROM users WHERE id = ?", (user_id,)).fetchone()
        balance = float(user["balance"] or 0)
        if balance < cost:
            return jsonify({"message": "余额不足，转盘每次需要 9.9 元", "balance": round(balance, 2)}), 400
        conn.execute("UPDATE users SET balance = balance - ? WHERE id = ?", (cost, user_id))
        conn.execute(
            "INSERT INTO balance_transactions (user_id, amount, kind, note, created_at) VALUES (?, ?, 'wheel', ?, ?)",
            (user_id, -cost, "趣味转盘", now),
        )
        if prize["type"] == "balance":
            conn.execute("UPDATE users SET balance = balance + ? WHERE id = ?", (prize["amount"], user_id))
            conn.execute(
                "INSERT INTO balance_transactions (user_id, amount, kind, note, created_at) VALUES (?, ?, 'wheel_prize', ?, ?)",
                (user_id, prize["amount"], prize["title"], now),
            )
        elif prize["type"] == "coupon":
            conn.execute(
                """
                INSERT INTO coupons
                (user_id, title, amount, min_amount, status, source, target_type, target_dish_id, discount_type, discount_rate, created_at)
                VALUES (?, ?, ?, ?, 'unused', 'wheel', ?, ?, ?, ?, ?)
                """,
                (
                    user_id,
                    prize["title"],
                    prize["amount"],
                    prize["min_amount"],
                    prize.get("target_type", "order"),
                    prize.get("target_dish_id"),
                    prize.get("discount_type", "amount"),
                    prize.get("discount_rate"),
                    now,
                ),
            )
        elif prize["type"] == "meal":
            dish = prize["dish"]
            conn.execute(
                """
                INSERT INTO coupons
                (user_id, title, amount, min_amount, status, source, target_type, target_dish_id, discount_type, created_at)
                VALUES (?, ?, ?, ?, 'unused', 'wheel', 'dish', ?, 'amount', ?)
                """,
                (user_id, prize["title"], dish["price"], 0, dish["id"], now),
            )
        conn.execute(
            "INSERT INTO wheel_records (user_id, prize_type, title, created_at) VALUES (?, ?, ?, ?)",
            (user_id, prize["type"], prize["title"], now),
        )
        balance = conn.execute("SELECT balance FROM users WHERE id = ?", (user_id,)).fetchone()["balance"]
    return jsonify(
        {
            "message": "抽奖完成",
            "prize": {"type": prize["type"], "title": prize["title"], "slot": prize["slot"]},
            "balance": round(float(balance or 0), 2),
        }
    )


@app.get("/api/my/complaints")
@login_required
def list_my_complaints():
    with get_db() as conn:
        rows = conn.execute(
            """
            SELECT complaints.*, users.username, users.nickname
            FROM complaints
            JOIN users ON users.id = complaints.user_id
            WHERE complaints.user_id = ?
            ORDER BY complaints.id DESC
            LIMIT 20
            """,
            (session["user_id"],),
        ).fetchall()
    return jsonify([serialize_complaint(row) for row in rows])


@app.post("/api/my/complaints")
@login_required
def create_my_complaint():
    data = request.get_json(silent=True) or {}
    body = data.get("body", "").strip()
    if not body:
        return jsonify({"message": "请输入投诉内容"}), 400
    now = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    with get_db() as conn:
        cursor = conn.execute(
            "INSERT INTO complaints (user_id, body, created_at) VALUES (?, ?, ?)",
            (session["user_id"], body, now),
        )
        row = conn.execute(
            """
            SELECT complaints.*, users.username, users.nickname
            FROM complaints
            JOIN users ON users.id = complaints.user_id
            WHERE complaints.id = ?
            """,
            (cursor.lastrowid,),
        ).fetchone()
    return jsonify(serialize_complaint(row)), 201


@app.get("/api/admin/wallet-records")
@admin_required
def admin_wallet_records():
    with get_db() as conn:
        withdrawals = conn.execute(
            """
            SELECT withdrawals.id, withdrawals.wechat, withdrawals.amount, withdrawals.status, withdrawals.created_at,
                   users.username, users.nickname
            FROM withdrawals
            JOIN users ON users.id = withdrawals.user_id
            ORDER BY withdrawals.id DESC
            LIMIT 80
            """
        ).fetchall()
        transactions = conn.execute(
            """
            SELECT balance_transactions.id, balance_transactions.amount, balance_transactions.kind,
                   balance_transactions.note, balance_transactions.created_at,
                   users.username, users.nickname
            FROM balance_transactions
            JOIN users ON users.id = balance_transactions.user_id
            ORDER BY balance_transactions.id DESC
            LIMIT 120
            """
        ).fetchall()
    return jsonify(
        {
            "withdrawals": [dict(row) for row in withdrawals],
            "transactions": [dict(row) for row in transactions],
        }
    )


@app.get("/api/admin/users")
@admin_required
def list_users():
    with get_db() as conn:
        rows = conn.execute(
            "SELECT id, username, nickname, role, balance, created_at FROM users ORDER BY id DESC"
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
        conn.execute("DELETE FROM balance_transactions WHERE user_id = ?", (user_id,))
        conn.execute("DELETE FROM withdrawals WHERE user_id = ?", (user_id,))
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
            ORDER BY
                CASE WHEN MAX(messages.id) IS NULL THEN 0 ELSE 1 END DESC,
                MAX(messages.id) DESC,
                users.id DESC
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
                    "last_message_id": user["last_message_id"] or 0,
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


@app.post("/api/admin/recharge")
@admin_required
def admin_recharge():
    data = request.get_json(silent=True) or {}
    username = data.get("username", "").strip()
    note = data.get("note", "").strip() or "商家充值"
    try:
        amount = round(float(data.get("amount", 0) or 0), 2)
    except (TypeError, ValueError):
        amount = 0
    if not username:
        return jsonify({"message": "请输入用户名"}), 400
    if amount == 0:
        return jsonify({"message": "充值金额不能为 0，可输入负数扣除余额"}), 400
    now = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    with get_db() as conn:
        user = conn.execute(
            "SELECT id, username, nickname, balance FROM users WHERE username = ?",
            (username,),
        ).fetchone()
        if user is None:
            return jsonify({"message": "用户不存在"}), 404
        new_balance = float(user["balance"] or 0) + amount
        if new_balance < 0:
            return jsonify({"message": "扣除后余额不能小于 0"}), 400
        conn.execute("UPDATE users SET balance = balance + ? WHERE id = ?", (amount, user["id"]))
        conn.execute(
            "INSERT INTO balance_transactions (user_id, amount, kind, note, created_at) VALUES (?, ?, ?, ?, ?)",
            (user["id"], amount, "recharge" if amount > 0 else "deduct", note, now),
        )
        balance = conn.execute("SELECT balance FROM users WHERE id = ?", (user["id"],)).fetchone()["balance"]
    return jsonify(
        {
            "message": "充值成功" if amount > 0 else "余额扣除成功",
            "username": user["username"],
            "nickname": user["nickname"] or user["username"],
            "amount": amount,
            "balance": round(float(balance or 0), 2),
        }
    )


@app.get("/api/admin/complaints")
@admin_required
def list_admin_complaints():
    with get_db() as conn:
        rows = conn.execute(
            """
            SELECT complaints.*, users.username, users.nickname
            FROM complaints
            JOIN users ON users.id = complaints.user_id
            ORDER BY complaints.id DESC
            LIMIT 100
            """
        ).fetchall()
    return jsonify([serialize_complaint(row) for row in rows])


@app.patch("/api/admin/complaints/<int:complaint_id>")
@admin_required
def reply_admin_complaint(complaint_id):
    data = request.get_json(silent=True) or {}
    reply = data.get("reply", "").strip()
    if not reply:
        return jsonify({"message": "请输入回复内容"}), 400
    now = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    with get_db() as conn:
        complaint = conn.execute("SELECT id FROM complaints WHERE id = ?", (complaint_id,)).fetchone()
        if complaint is None:
            return jsonify({"message": "投诉不存在"}), 404
        conn.execute(
            "UPDATE complaints SET reply = ?, status = '已回复', replied_at = ? WHERE id = ?",
            (reply, now, complaint_id),
        )
    return jsonify({"message": "已回复投诉", "reply": reply, "replied_at": now})


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
        mains = [dish for dish in MENU if dish["category"] == "主厨西餐"]
        desserts = [dish for dish in MENU if dish["category"] == "甜品"]
        staples = [dish for dish in MENU if dish["category"] == "浪漫主食"]
        starters = [dish for dish in MENU if dish["category"] in ("前菜沙拉", "精致小食")]
        drinks = [dish for dish in MENU if dish["category"] == "酒水饮品"]
        selected = [
            random.choice(mains),
            random.choice(staples),
            random.choice(starters),
            random.choice(desserts),
            random.choice(drinks),
        ]
    elif "辣" in message:
        selected_ids = [29, 51, 64]
    elif "清淡" in message or "不辣" in message:
        selected_ids = [3, 16, 63]
    elif "饮" in message or "喝" in message:
        selected_ids = [58, 59, 60]
    elif "两" in message or "2" in message:
        selected_ids = [1, 43, 59]
    else:
        selected_ids = [2, 41, 57]

    if not blind_box:
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
    try:
        api_key.encode("ascii")
    except UnicodeEncodeError:
        return jsonify({"message": "智谱 API Key 配置不正确，请在服务器环境变量 ZHIPU_API_KEY 中填写真实英文/数字 Key，不要使用中文占位符。"}), 503

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
                    "你是雨石屋的 AI 点餐助手。用户正常寒暄时就自然聊天，不要主动生成菜单。"
                    "只有用户明确表达想点餐、推荐、盲盒、预算、人数、口味或忌口时，"
                    "才围绕本店菜单搭配菜品并给出总价估算。回复要简洁、亲切，适合手机点餐页面展示。\n\n"
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
            "SELECT id, status, payable FROM orders WHERE id = ? AND user_id = ?",
            (order_id, user_id),
        ).fetchone()
        if order is None:
            return jsonify({"message": "订单不存在"}), 404
        if order["status"] in {"已完成", "已取消"}:
            return jsonify({"message": "当前订单不能取消"}), 400
        conn.execute("UPDATE orders SET status = '已取消' WHERE id = ?", (order_id,))
        refund = float(order["payable"] or 0)
        if refund > 0:
            now = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
            conn.execute("UPDATE users SET balance = balance + ? WHERE id = ?", (refund, user_id))
            conn.execute(
                "INSERT INTO balance_transactions (user_id, amount, kind, note, created_at) VALUES (?, ?, 'refund', ?, ?)",
                (user_id, refund, "订单 #{} 取消退款".format(order_id), now),
            )
        conn.execute(
            "UPDATE coupons SET status = 'unused', used_at = NULL, order_id = NULL WHERE order_id = ?",
            (order_id,),
        )
    return jsonify(fetch_orders("WHERE id = ?", (order_id,))[0])


init_db()


if __name__ == "__main__":
    port = int(os.environ.get("PORT", 5000))
    app.run(host="0.0.0.0", port=port, debug=False, use_reloader=False)
