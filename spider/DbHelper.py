#-*-coding:utf-8-*-
# Author : EricZhao

import pymysql.cursors
import DbConfig


class DBHelper:
    con = None
    isClose = False

    def __init__(self):
        pass

    def connect(self):
        self.con = pymysql.connect(host=DbConfig.host,
                       port = DbConfig.port,
                       user = DbConfig.user,
                       password = DbConfig.password,
                       db = DbConfig.db,
                       charset = DbConfig.charset,
                       cursorclass = pymysql.cursors.DictCursor)

    def query_one(self, sql, params):
        if self.con is None:
            raise Exception("Not connected to DB")
        with self.con.cursor() as cursor:
            cursor.execute(sql, params)
            rs = cursor.fetchone()
            return rs

    def query_all(self, sql, params):
        if self.con is None:
            raise Exception("Not connected to DB")
        with self.con.cursor() as cursor:
            cursor.execute(sql, params)
            rs = cursor.fetchall()
            return rs

    def insert_update_delete(self, sql, params):
        if self.con is None:
            raise Exception("Not connected to DB")
        if self.isClose:
            self.connect()
        with self.con.cursor() as cursor:
            effected_rows = cursor.execute(sql, params)
            return effected_rows

    def commit(self):
        if self.con is None:
            raise Exception("Not connected to DB")
        self.con.commit()

    def close(self):
        if self.con is None:
            raise Exception("Not connected to DB")
        self.commit()
        self.con.close()
        isClose = True
