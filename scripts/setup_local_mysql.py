"""Install an isolated MySQL 8.4 on Windows, without changing Windows services."""
import os
import secrets
import subprocess
import time
import urllib.request
import zipfile
from pathlib import Path
import pymysql
from common import ROOT

VERSION='8.4.13'
HOME=Path(os.environ['LOCALAPPDATA'])/'volleyball-mysql'
BASE=HOME/f'mysql-{VERSION}-winx64'
DATA=HOME/'db'

def start():
    subprocess.Popen([str(BASE/'bin/mysqld.exe'),'--no-defaults',f'--basedir={BASE}',
        f'--datadir={DATA}','--port=3307','--bind-address=127.0.0.1',
        '--mysqlx=OFF','--log-error=mysql-error.log'],creationflags=subprocess.CREATE_NO_WINDOW)

def main():
    if (ROOT/'.env').exists():
        from common import engine
        try:
            with engine().connect():
                print('Project MySQL is already running.'); return
        except Exception:
            if not (BASE/'bin/mysqld.exe').exists():
                raise RuntimeError('Existing .env found. Check your existing MySQL setup.')
            start()
            for _ in range(40):
                try:
                    with engine().connect():
                        print('Project MySQL restarted.'); return
                except Exception:
                    time.sleep(0.5)
            raise RuntimeError(f'Cannot start MySQL. Check {DATA}/mysql-error.log')
    HOME.mkdir(parents=True,exist_ok=True)
    if not (BASE/'bin/mysqld.exe').exists():
        archive=HOME/'mysql.zip'
        if not archive.exists():
            print('Downloading official MySQL ZIP (about 270 MB)...')
            urllib.request.urlretrieve(f'https://cdn.mysql.com/Downloads/MySQL-8.4/mysql-{VERSION}-winx64.zip',archive)
        with zipfile.ZipFile(archive) as z:
            z.extractall(HOME)
    if not (DATA/'mysql').exists():
        subprocess.run([str(BASE/'bin/mysqld.exe'),'--no-defaults','--initialize-insecure',f'--basedir={BASE}',f'--datadir={DATA}'],check=True)
    for attempt in range(40):
        try:
            conn=pymysql.connect(host='127.0.0.1',port=3307,user='root',password='')
            break
        except pymysql.err.OperationalError as error:
            if error.args[0] == 1045:
                raise RuntimeError('Root already has a password. Configure .env for your existing database.') from error
            if attempt==0:
                start()
            time.sleep(0.5)
    else:
        raise RuntimeError(f'Cannot connect. Check {DATA}/mysql-error.log')
    root_password=secrets.token_urlsafe(32)
    app_password=secrets.token_urlsafe(32)
    runtime=ROOT/'.runtime'; runtime.mkdir(exist_ok=True)
    # Persist credentials before applying them so interrupted setup is recoverable.
    (runtime/'admin.env').write_text(f'MYSQL_ROOT_PASSWORD={root_password}\n',encoding='utf-8')
    with conn.cursor() as c:
        c.execute("ALTER USER 'root'@'localhost' IDENTIFIED BY %s",(root_password,))
        c.execute("CREATE USER IF NOT EXISTS 'volleyball_user'@'localhost' IDENTIFIED BY %s",(app_password,))
        c.execute("GRANT ALL PRIVILEGES ON volleyball_db.* TO 'volleyball_user'@'localhost'")
    conn.close()
    (ROOT/'.env').write_text(f'DB_HOST=127.0.0.1\nDB_PORT=3307\nDB_USER=volleyball_user\nDB_PASSWORD={app_password}\nDB_NAME=volleyball_db\n',encoding='utf-8')
    print('MySQL ready at 127.0.0.1:3307. Passwords saved only in ignored local files.')

if __name__=='__main__':
    main()
