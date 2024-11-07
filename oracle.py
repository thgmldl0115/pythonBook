import cx_Oracle
conn = cx_Oracle.connect("book", "book", "localhost:1521/xe")
cur = conn.cursor()

sql = """

       SELECT * FROM tb_user

"""

cur.execute(sql)
conn.commit()




