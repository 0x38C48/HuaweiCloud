import os
import pymysql
from dotenv import load_dotenv
from pymysql.cursors import DictCursor

load_dotenv()

class GaussDBConnector:
    def __init__(self):
        self.host = os.getenv("DB_HOST")
        self.port = int(os.getenv("DB_PORT"))
        self.user = os.getenv("DB_USER")
        self.password = os.getenv("DB_PASSWORD")
        self.db = os.getenv("DB_NAME")
        self.connection = None
        self.cursor = None     

    def connect(self):
        try:
            self.connection = pymysql.connect(
                host=self.host,
                port=self.port,
                user=self.user,
                password=self.password,
                database=self.db,
                charset="utf8mb4",
                cursorclass=DictCursor 
            )
            self.cursor = self.connection.cursor()
            print("GaussDB 连接成功！")
        except Exception as e:
            print(f"连接失败：{str(e)}")
            raise 

    def close(self):
        if self.cursor:
            self.cursor.close()
        if self.connection and self.connection.open:
            self.connection.close()
            print("数据库连接已关闭")

    def __enter__(self):
        self.connect()
        return self

    def __exit__(self, exc_type, exc_val, exc_tb):
        self.close()