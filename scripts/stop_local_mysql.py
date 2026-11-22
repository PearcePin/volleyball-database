"""Gracefully stop only the isolated project MySQL server."""
import os
from pathlib import Path
import pymysql
from dotenv import dotenv_values
from common import ROOT

def main():
    if os.getenv('DB_HOST')!='127.0.0.1' or os.getenv('DB_PORT')!='3307':
        raise RuntimeError('This command only stops the project server on 127.0.0.1:3307')
    password=dotenv_values(ROOT/'.runtime/admin.env')['MYSQL_ROOT_PASSWORD']
    conn=pymysql.connect(host='127.0.0.1',port=3307,user='root',password=password)
    with conn.cursor() as cursor:
        cursor.execute('SHUTDOWN')
    conn.close()
    print('Project MySQL stopped. Data files are preserved.')

if __name__=='__main__':
    main()
