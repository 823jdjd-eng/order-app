# 拾味小馆点餐网站

一个用 Flask 写的移动端点餐网站，包含点餐、购物车、登录注册、商家后台、订单状态和 AI 智能体预留界面。

## 本地运行

```bash
pip install -r requirements.txt
python app.py
```

访问：

```text
http://127.0.0.1:5000
```

商家后台：

```text
http://127.0.0.1:5000/admin
```

默认商家账号：

```text
admin / admin123
```

## Render 部署

Build Command:

```bash
pip install -r requirements.txt
```

Start Command:

```bash
gunicorn app:app
```
