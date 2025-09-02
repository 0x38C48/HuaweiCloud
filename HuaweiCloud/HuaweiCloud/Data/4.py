from db_connect import GaussDBConnector

class HomeDataOperator:
    def __init__(self):
        self.db_connector = GaussDBConnector()

    def create_user_home_data(self, user_id, data_date, home_status):
        """新增用户家居数据"""
        sql = """
            INSERT INTO user_home_data (user_id, data_date, home_status) #用户id,日期，家庭特殊情况（老人/小孩/无）
            VALUES (%s, %s, %s)
        """
        try:
            with self.db_connector as db:
                db.cursor.execute(sql, (user_id, data_date, home_status))
                db.connection.commit()
                print(f"✅ 新增成功，记录ID：{db.cursor.lastrowid}")
                return db.cursor.lastrowid
        except Exception as e:
            print(f"❌ 新增失败：{str(e)}")
            db.connection.rollback() 
            return None

    def get_user_home_data(self, user_id, data_date=None):
        """查询用户家居数据（支持按日期筛选）"""
        sql = "SELECT * FROM user_home_data WHERE user_id = %s"
        params = [user_id]
        if data_date:
            sql += " AND data_date = %s"
            params.append(data_date)
        
        try:
            with self.db_connector as db:
                db.cursor.execute(sql, params)
                result = db.cursor.fetchall()  # 获取所有匹配记录
                print(f"✅ 查询到 {len(result)} 条记录")
                return result
        except Exception as e:
            print(f"❌ 查询失败：{str(e)}")
            return None

    def update_home_status(self, record_id, new_home_status):
        """更新家居状态"""
        sql = """
            UPDATE user_home_data 
            SET home_status = %s, update_time = NOW()
            WHERE id = %s
        """
        try:
            with self.db_connector as db:
                affected_rows = db.cursor.execute(sql, (new_home_status, record_id))
                db.connection.commit()
                if affected_rows > 0:
                    print(f"✅ 更新成功，影响 {affected_rows} 条记录")
                    return True
                else:
                    print("⚠️ 未找到待更新的记录")
                    return False
        except Exception as e:
            print(f"❌ 更新失败：{str(e)}")
            db.connection.rollback()
            return False

    def delete_user_home_data(self, record_id):
        """删除指定记录"""
        sql = "DELETE FROM user_home_data WHERE id = %s"
        try:
            with self.db_connector as db:
                affected_rows = db.cursor.execute(sql, [record_id])
                db.connection.commit()
                if affected_rows > 0:
                    print(f"✅ 删除成功，影响 {affected_rows} 条记录")
                    return True
                else:
                    print("⚠️ 未找到待删除的记录")
                    return False
        except Exception as e:
            print(f"❌ 删除失败：{str(e)}")
            db.connection.rollback()
            return False
