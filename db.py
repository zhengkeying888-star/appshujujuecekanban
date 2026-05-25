"""PostgreSQL 数据库连接管理（Neon on Vercel）

环境变量要求：
  DATABASE_URL — Neon pooled connection string
  示例: postgresql://user:pass@host-pooler.neon.tech/dbname?sslmode=require

Neon 特定要求：
  1. 必须使用 pooled connection（hostname 含 -pooler.）
  2. 必须携带 ?sslmode=require
  3. Python 使用 psycopg v3（pip install psycopg）
"""
import os
import psycopg
from contextlib import contextmanager

DEFAULT_DB_URL = os.environ.get('DATABASE_URL', '')


def get_connection_string() -> str:
    """获取数据库连接字符串，优先从环境变量读取"""
    url = os.environ.get('DATABASE_URL', '')
    if not url:
        raise RuntimeError(
            "DATABASE_URL 环境变量未设置。\n"
            "请从 Vercel Dashboard → Storage → Neon → .env.local 中复制连接字符串，\n"
            "并执行: export DATABASE_URL='postgresql://...'"
        )
    # 确保 Neon 连接携带 sslmode=require
    if 'sslmode=' not in url:
        sep = '&' if '?' in url else '?'
        url = f"{url}{sep}sslmode=require"
    return url


@contextmanager
def get_conn():
    """获取数据库连接的上下文管理器"""
    conn = psycopg.connect(get_connection_string())
    try:
        yield conn
    finally:
        conn.close()


def execute(sql: str, params=None, fetch=False):
    """执行单条 SQL，可选返回结果"""
    with get_conn() as conn:
        with conn.cursor() as cur:
            cur.execute(sql, params)
            if fetch:
                return cur.fetchall()
            conn.commit()


def fetch_one(sql: str, params=None):
    """执行查询并返回单条记录"""
    with get_conn() as conn:
        with conn.cursor() as cur:
            cur.execute(sql, params)
            return cur.fetchone()


def fetch_all(sql: str, params=None):
    """执行查询并返回全部记录"""
    with get_conn() as conn:
        with conn.cursor() as cur:
            cur.execute(sql, params)
            return cur.fetchall()


def table_exists(table_name: str) -> bool:
    """检查表是否存在"""
    row = fetch_one(
        "SELECT 1 FROM information_schema.tables WHERE table_name = %s",
        (table_name,)
    )
    return row is not None


def count_rows(table_name: str) -> int:
    """获取表行数"""
    row = fetch_one(f"SELECT COUNT(*) FROM {table_name}")
    return row[0] if row else 0


def query_to_df(sql: str, params=None):
    """执行 SQL 查询并返回 pandas DataFrame（兼容 psycopg v3）"""
    import pandas as pd
    with get_conn() as conn:
        with conn.cursor() as cur:
            cur.execute(sql, params)
            cols = [desc[0] for desc in cur.description] if cur.description else []
            rows = cur.fetchall()
    return pd.DataFrame(rows, columns=cols)
