import lorem
import psycopg2
from psycopg2 import extras
from psycopg2.extensions import connection as _connection
from datetime import datetime
import time
import random


def insert_tasks(pg_conn: _connection):
    cur = pg_conn.cursor()

    tasks_list = [[lorem.sentence(), lorem.paragraph(), 'OP', 5, datetime.now(), datetime.now()] for _ in range(25000)]
    print(tasks_list)
    sql = """INSERT INTO tasks_task (
        title,
        description,
        status,
        owner_id,
        created_at,
        updated_at
    ) VALUES %s ON CONFLICT (id) DO NOTHING"""
    extras.execute_values(cur, sql, tasks_list, template=None, page_size=2000)
    pg_conn.commit()


def insert_time_logs(pg_conn: _connection):
    cur = pg_conn.cursor()
    
    time_log_list = [[
        random.randint(1, 25000),
        5,
        datetime.now(),
        None,
        random.randint(2, 120),
        datetime.now(),
        datetime.now(),
        True,
    ] for _ in range(50000)]
    print(time_log_list)
    sql = """INSERT INTO tasks_taskduration (
        task_id,
        owner_id,
        start_working_datetime,
        stop_working_datetime,
        duration,
        created_at,
        updated_at,
        timer_on
    ) VALUES %s ON CONFLICT (id) DO NOTHING"""
    extras.execute_values(cur, sql, time_log_list, template=None, page_size=2000)
    pg_conn.commit()


if __name__ == '__main__':
    dsn = {
        'dbname': 'tasks_db',
        'user': 'postgres',
        'password': '1234',
        'host': '127.0.0.1',
        'port': '5432'
    }

    with psycopg2.connect(**dsn, cursor_factory=extras.DictCursor) as pg_conn:
        insert_tasks(pg_conn)
        insert_time_logs(pg_conn)
