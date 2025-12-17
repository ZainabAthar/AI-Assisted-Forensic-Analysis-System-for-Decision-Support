from flask import Flask,g
from . import db
import sqlite3
import pytest
import os
DB_SCHEMA_PATH=os.path.join(os.getcwd(),'schema.sql')
@pytest.fixture
def app():
    '''Creates test app instance.'''
    app=Flask(__name__)
    app.config.update({
        'TESTING':True,
        'DB_PATH':':memory:',
        'DB_SCHEMA_PATH':os.path.join(os.getcwd(),'schema.sql')
    })
    yield app
@pytest.fixture
def mock_db(app):
    '''Mocks db.get_db() to use a test database connection.'''
    og_get_db=db.get_db
    def mock_get_db():
        if not hasattr(g,'_test_database'):
            test_con=sqlite3.connect(app.config['DB_PATH'])
            test_con.row_factory=sqlite3.Row
            with open(app.config['DB_SCHEMA_PATH'],'r')as db_schema_script:
                test_con.executescript(db_schema_script.read())
            test_con.commit()
            g._test_database=test_con
        return g._test_database
    db.get_db=mock_get_db
    yield
    db.get_db=og_get_db
class TestDBConnection:
    '''Tests database connection access functions.'''
    def test_get_db_inititial_instance(self,app):
        with app.app_context():
            db_con=db.get_db()
            assert db_con is not None
    def test_get_db_multiple_instances(self,app):
        with app.app_context():
            db_con_one=db.get_db()
            db_con_two=db.get_db()
            assert db_con_one is db_con_two
            assert db_con_one is not None
    def test_close_db(self,app):
        with app.app_context():
            db_con=db.get_db()
            assert db_con is not None
            db.close_db(None)
            assert db.get_db() is not db_con
@pytest.mark.usefixtures('mock_db')
class TestDBQuery:
    '''Tests database query utility function.'''
    def test_db_query_null(self,app):
        with app.app_context():
            assert db.query(None)is None
    def test_db_query_single(self,app):
        with app.app_context():
            db.get_db().execute("INSERT INTO Users(user_id,username,password) VALUES(0,'user','password');")
            db.get_db().commit()
            ret=db.query("SELECT * FROM Users WHERE username='user';")
            assert ret is not None
            assert len(ret)==1
            assert ret[0]['user_id']==0
            assert ret[0]['username']=='user'
            assert ret[0]['password']=='password'
    def test_db_query_multiple(self,app):
        with app.app_context():
            db.get_db().execute("INSERT INTO Users(username,password) VALUES('user_one','password_one');")
            db.get_db().execute("INSERT INTO Users(username,password) VALUES('user_two','password_two');")
            db.get_db().commit()
            ret=db.query('SELECT user_id,username FROM Users ORDER BY user_id ASC;')
            assert ret is not None
            assert len(ret)==2
            assert ret[0]['username']=='user_one'
            assert ret[1]['username']=='user_two'
@pytest.mark.usefixtures('mock_db')
class TestDBUser:
    '''Tests database interface to the `Users` table.'''
    def test_db_usr_id_valid(self,app):
        with app.app_context():
            db.get_db().execute("INSERT INTO Users(username,password) VALUES('user','password');")
            db.get_db().commit()
            assert db.usr_id('user')==1
    def test_db_usr_id_invalid(self,app):
        with app.app_context():
            assert db.usr_id('notauser')is None
            assert db.usr_id(None)is None
    def test_db_usr_name_valid(self,app):
        with app.app_context():
            db.get_db().execute("INSERT INTO Users(user_id,username,password) VALUES(0,'user','password');")
            db.get_db().commit()
            assert db.usr_name(0)=='user'
    def test_db_usr_auth_valid(self,app):
        with app.app_context():
            db.get_db().execute("INSERT INTO Users(username,password) VALUES('user','password');") 
            db.get_db().commit()
            assert db.usr_auth('user','password')is True
    def test_db_usr_auth_invalid(self,app):
        with app.app_context():
            db.get_db().execute("INSERT INTO Users(username,password) VALUES('user','password');")
            db.get_db().commit()
            assert db.usr_auth('user','wrongpassword')is False
    def test_db_usr_reg_not_taken(self,app):
        with app.app_context():
            _,ret=db.usr_reg('userA','password')
            assert ret is db.RET.SUCCESS
            #TODO test validation when implemented.
            #assert db.usr_reg('','password')is False
            #assert db.usr_reg('userB','')is False
            #...
    def test_db_usr_reg_taken(self,app):
        with app.app_context():
            db.usr_reg('user','password')
            _,ret=db.usr_reg('user','anotherpassword')
            assert ret is db.RET.ERR_USRNAME_TAKEN
            ret=db.query("SELECT COUNT(user_id) FROM Users WHERE username='user';",one=True)
            assert ret is not None
            assert ret[0]==1
@pytest.mark.usefixtures('mock_db')
class TestDBSession:
    '''Tests database interface to the `Sessions` table.'''
    def test_db_ssn_new_valid(self,app):
        with app.app_context():
            _,ret=db.ssn_new('127.0.0.1')
            assert ret is db.RET.SUCCESS
            ret=db.query("SELECT COUNT(session_id) FROM Sessions WHERE client_addr='127.0.0.1';",one=True)
            assert ret is not None
            assert ret[0]==1
    def test_db_ssn_usr_bind(self,app):
        with app.app_context():
            sid,_=db.ssn_new('127.0.0.1')
            uid,_=db.usr_reg('user','password')
            assert db.ssn_usr_bind(sid=sid,uid=uid)is db.RET.SUCCESS
            ret=db.query("SELECT COUNT(session_id) FROM Sessions WHERE session_id=? AND user_id=?;",(sid,uid),one=True)
            assert ret is not None
            assert ret[0]==1
    def test_db_ssn_rm(self,app):
        with app.app_context():
            sid,_=db.ssn_new('127.0.0.1')
            db.ssn_rm(sid)
            ret=db.query('SELECT COUNT(*) FROM Sessions;',one=True)
            assert ret is not None
            assert ret[0]==0
    def test_db_ssn_usr_id(self,app):
        with app.app_context():
            sid,_=db.ssn_new('127.0.0.1')
            uid,_=db.usr_reg('user','password')
            db.ssn_usr_bind(sid=sid,uid=uid)
            assert db.ssn_usr_id(sid)==uid
    def test_db_usr_ssn_n(self,app):
        with app.app_context():
            sid0,_=db.ssn_new('127.0.0.1')
            sid1,_=db.ssn_new('127.0.0.1')
            uid,_=db.usr_reg('user','password')
            assert db.usr_ssn_n('user')==0
            db.ssn_usr_bind(sid=sid0,uid=uid)
            assert db.usr_ssn_n('user')==1
            db.ssn_usr_bind(sid=sid1,uid=uid)
            assert db.usr_ssn_n('user')==2
            db.ssn_rm(sid1)
            assert db.usr_ssn_n('user')==1
            #If a usr_rm function is implemented, test that here.
#    def test_db_req_log(self,app):
#        with app.app_context():
    
