from flask import g,current_app,flash
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
    if not query:
        return None
    params=params or[]
    cur=get_db().execute(query,params)
    ret=cur.fetchone()if one else cur.fetchall()
    cur.close()
    return ret or None
def usr_id(usrname):
    ret=query('SELECT user_id FROM Users WHERE username=?;',(usrname,),one=True) 
    return ret[0]if ret else None
def usr_name(usr_id):
    ret=query('SELECT username FROM Users WHERE user_id=?;',(usr_id,),one=True)
    return ret[0]if ret else None
def usr_ssn_n(usrname):
    ret=query('SELECT COUNT(*) FROM Sessions WHERE user_id=?;',(usr_id(usrname),),one=True) 
    return ret[0]if ret else 0
def usr_auth(usrname,pwd):
    ret=query('SELECT COUNT(*) FROM Users WHERE username=? AND password=?;',(usrname,pwd,),one=True)
    return(ret[0]==1)if ret else False
def usr_reg(usrname,pwd):
    if not usrname or not pwd:#TODO replace this with more general validation.
        flash('Invalid username or password.','danger')
        return False
    db=get_db()
    try:
        #Check whether username taken.
        ret=query('SELECT COUNT(*) FROM Users WHERE username=?;',(usrname,),one=True)
        if ret and ret[0]>0:#error: username taken.
            flash('Username taken.','danger')
            return False
        #Insert new user entry.
        db.execute('INSERT INTO Users(username,password) VALUES(?,?);',(usrname,pwd))
        db.commit()
        return True
    except sqlite3.Error as err:
        db.rollback()
        print(f'Database Error: \"{err}\"')#TODO maintain error codes and IDs.
        flash('Internal error. Try again later.','danger')
        return False
def ssn_new(usrname):
    if not usrname:
        return None
    db=get_db()
    try:
        uid=usr_id(usrname)
        db.execute('INSERT INTO Sessions(user_id) VALUES(?);',(uid,))
        ret=query('SELECT session_id FROM Sessions WHERE user_id=?',(uid,),one=True)
        db.commit()
        return ret[0]if ret else None
    except sqlite3.Error as err:
        db.rollback()
        print(f'Database Error: \"{err}\"')
        return None
def ssn_rm(ssn_id):
    if not ssn_id:
        return False
    db=get_db()
    try:
        db.execute('DELETE FROM Sessions WHERE session_id=?',(ssn_id,))
        db.commit()
        return True
    except sqlite3.Error as err:
        db.rollback()
        print(f'Database Error: \"{err}\"')
def ssn_usr_id(ssn_id):
    if not ssn_id:
        return None
    ret=query('SELECT user_id FROM Sessions WHERE session_id=?;',(ssn_id,),one=True)
    return ret[0]if ret else None
