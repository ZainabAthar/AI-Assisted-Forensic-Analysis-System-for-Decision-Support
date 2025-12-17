from flask import g,current_app
from enum import Enum
import sqlite3
def get_db():
    db=getattr(g,'_database',None)
    if db is None:
        db=g._database=sqlite3.connect(current_app.config['DB_PATH'])
        db.row_factory=sqlite3.Row#to return dicts instead of tuples.
    return db
def close_db(exception):#Terminates database connection per-request.
    db=getattr(g,'_database',None)
    if db is not None:
        db.close()
        g._database=None
def query(query,params=None,one=False):
    if query is None:
        return None
    params=params or[]
    cur=get_db().execute(query,params)
    ret=cur.fetchone()if one is True else cur.fetchall()
    cur.close()
    return ret or None
class RET(Enum):
    SUCCESS=0
    ERR_GENERIC=1
    ERR_INVALID_INPUT=2
    ERR_USRNAME_TAKEN=3
def usr_id(usrname):
    ret=query('SELECT user_id FROM Users WHERE username=?;',(usrname,),one=True) 
    return ret[0]if ret is not None else None
def usr_name(uid):
    ret=query('SELECT username FROM Users WHERE user_id=?;',(uid,),one=True)
    return ret[0]if ret is not None else None
def usr_ssn_n(usrname):
    ret=query('SELECT COUNT(*) FROM Sessions WHERE user_id=?;',(usr_id(usrname),),one=True) 
    return ret[0]if ret is not None else 0
def usr_auth(usrname,pwd):
    ret=query('SELECT COUNT(*) FROM Users WHERE username=? AND password=?;',(usrname,pwd,),one=True)
    return(ret[0]==1)if ret is not None else False
def usr_reg(usrname,pwd):
    if usrname is None or pwd is None:#TODO replace this with more general validation.
        return(None,RET.ERR_INVALID_INPUT)
    db=get_db()
    try:
        #Check whether username taken.
        ret=query('SELECT COUNT(*) FROM Users WHERE username=?;',(usrname,),one=True)
        if ret is not None and ret[0]>0:#error: username taken.
            return(None,RET.ERR_USRNAME_TAKEN)
        #Insert new user entry.
        cur=db.cursor()
        cur.execute('INSERT INTO Users(username,password) VALUES(?,?);',(usrname,pwd))
        db.commit()
        return(cur.lastrowid,RET.SUCCESS)
    except sqlite3.Error as err:
        db.rollback()
        print(f'Database Error: \"{err}\"')#TODO maintain error codes and IDs.
        return(None,RET.ERR_GENERIC)#TODO also generate & log a unique error code.
def ssn_new(addr):
    if addr is None:
        return(None,RET.ERR_INVALID_INPUT)
    db=get_db()
    try:
        cur=db.cursor()
        cur.execute('INSERT INTO Sessions(user_id,client_addr) VALUES(NULL,?);',(addr,))
        ssn_id=cur.lastrowid
        cur.close()
        db.commit()
        return(ssn_id,RET.SUCCESS)
    except sqlite3.Error as err:
        db.rollback()
        print(f'Database Error: \"{err}\"')
        return(None,RET.ERR_GENERIC)
def ssn_usr_bind(sid,uid):
    if sid is None:
        return RET.ERR_INVALID_INPUT
    db=get_db()
    try:
        cur=db.cursor()
        cur.execute('UPDATE Sessions SET user_id=? WHERE session_id=?',(uid,sid))
        cur.close()
        db.commit()
        return RET.SUCCESS
    except sqlite3.Error as err:
        db.rollback()
        print(f'Database Error: \"{err}\"')
        return RET.ERR_GENERIC
def ssn_rm(sid):
    if sid is None:
        return RET.ERR_INVALID_INPUT
    db=get_db()
    try:
        db.execute('DELETE FROM Sessions WHERE session_id=?',(sid,))
        db.execute('DELETE FROM Requests WHERE session_id=?',(sid,))
        db.commit()
        return RET.SUCCESS
    except sqlite3.Error as err:
        db.rollback()
        print(f'Database Error: \"{err}\"')
        return RET.ERR_GENERIC
def ssn_usr_id(ssn_id):
    if ssn_id is None:
        return None
    ret=query('SELECT user_id FROM Sessions WHERE session_id=?;',(ssn_id,),one=True)
    return ret[0]if ret is not None else None
def req_log(sid,mthd):
    if mthd is None:
        return RET.ERR_INVALID_INPUT
    db=get_db()
    try:
        cur=db.cursor()
        cur.execute('INSERT INTO Requests(session_id,method) VALUES(?,?);',(sid,mthd))
        cur.close()
        db.commit()
        return RET.SUCCESS
    except sqlite3.Error as err:
        db.rollback()
        print(f'Database Error: \"{err}\"')
        return RET.ERR_GENERIC
