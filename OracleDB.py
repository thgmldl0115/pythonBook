import cx_Oracle


class DBManager:
    def __init__(self):
        self.conn = None
        self.get_connection()

    def get_connection(self,user='book',  pw='book', host='localhost', port='1521'):
        try:
            self.conn = cx_Oracle.connect(user, pw, f"{host}:{port}/xe")
            print("접속됨.")
        except cx_Oracle.DatabaseError as e:
            print("Database connection error:", e)
            self.conn = None

    def __del__(self):
        # 소멸자: 객체가 삭제될 때 연결을 닫음
        try:
            if self.conn:
                self.conn.close()
                print("접속을 종료함.")
        except cx_Oracle.DatabaseError as e:
            # 연결 해제 오류 처리
            print("데이터베이스 연결 종료 오류:", str(e))

    def execute_query(self, query, param=None):
        """
        주어진 쿼리를 실행하고 선택적으로 파라미터를 전달함.
        INSERT/UPDATE/DELETE 쿼리에 대해서는 커밋 수행.
        """
        if self.conn is None:
            # 연결이 없을 때 알림 메시지
            print("데이터베이스 연결이 설정되지 않았습니다.")
            return None

        try:
            cursor = self.conn.cursor()
            # 파라미터가 있는 경우와 없는 경우 처리
            if param:
                cursor.execute(query, param)
            else:
                cursor.execute(query)

            # INSERT, UPDATE, DELETE 쿼리에 대해서만 커밋 수행
            if query.strip().upper().startswith(("INSERT", "UPDATE", "DELETE")):
                self.conn.commit()

            return cursor  # 커서를 반환하고, 호출한 쪽에서 닫음
        except cx_Oracle.DatabaseError as e:
            # 쿼리 실행 오류 처리
            print("쿼리 실행 오류:", e)
            self.conn.rollback()
            return None

    def fetch_one(self, query, param=None):
        """
        쿼리 결과에서 한 줄만 가져옴.
        """
        cursor = self.execute_query(query, param)
        result = cursor.fetchone() if cursor else None
        return result

    def fetch_all(self, query, param=None):
        """
        쿼리 결과에서 모든 줄을 가져옴.
        """
        cursor = self.execute_query(query, param)
        if cursor is not None:
            results = cursor.fetchall()
            cursor.close()  # 데이터를 가져온 후 커서를 닫음
            return results
        else:
            print("쿼리 실행에 실패하여 결과를 가져올 수 없습니다.")
            return []  # 오류가 발생하면 빈 리스트 반환


if __name__ == '__main__':
    db = DBManager()

    # # 예제: INSERT 쿼리 실행
    # db.execute_query("INSERT INTO tb_user (user_id, user_pw, user_nm) VALUES (:1, :2, :3)"
    #                  , ("test", "test", "test"))
    #
    # # 예제: SELECT 쿼리 실행 후 결과 출력
    # results = db.fetch_all("SELECT * FROM tb_user")
    # for row in results:
    #     print(row)
    #
    # userId = 'aaaa'
    # sql1 = "SELECT user_pw FROM tb_user WHERE user_id = :1"
    # pw = db.fetch_all(sql1, [userId])
    # print(pw)

    results = db.fetch_all("""
                            SELECT b_end_yn, b_title, b_author, 
                            CASE WHEN b_category = '000' THEN '총류, 컴퓨터과학'
                                 WHEN b_category = '100' THEN '철학, 심리학, 윤리학'
                                 WHEN b_category = '200' THEN '종교'
                                 WHEN b_category = '300' THEN '사회과학'
                                 WHEN b_category = '400' THEN '어학'
                                 WHEN b_category = '500' THEN '순수과학'
                                 WHEN b_category = '600' THEN '기술과학'
                                 WHEN b_category = '700' THEN '예술'
                                 WHEN b_category = '800' THEN '문학'
                                 WHEN b_category = '900' THEN '역사'
                                 ELSE '기타'
                            END as b_category, 
                            b_page, b_dicount, 
                            TO_CHAR(b_create_dt, 'YYYY-MM-DD') as b_create_dt, 
                            TO_CHAR(b_update_dt, 'YYYY-MM-DD') as b_update_dt
                    FROM tb_book
                    WHERE user_id='aaaa'
                            """)
    for row in results:
        print(row)


