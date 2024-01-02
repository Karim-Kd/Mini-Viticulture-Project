from flask import g
import sqlite3

def connect_to_database():
    sql = sqlite3.connect('E:\Projects\Viticulture-MiniProject/viticulture.db')
    sql.row_factory = sqlite3.Row
    return sql


def get_database():
    if not hasattr(g, 'viticulture_db'):
        g.viticulture_db = connect_to_database()
    return g.viticulture_db  