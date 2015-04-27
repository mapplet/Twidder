import sqlite3
import uuid

from flask import g
from contextlib import closing
from __init__ import app

DATABASE = '/Users/Martin/Documents/Skolan/LiU/VT-15/TDDD97/Twidder/Twidder/database.db'


def connect_db():
    db = sqlite3.connect(DATABASE)
    #db.row_factory = sqlite3.Row
    db.cursor().execute('PRAGMA FOREIGN_KEYS = ON')
    return db

def get_db():
    db = getattr(g, 'db', None)
    if db is None:
        db = g.db = connect_db()
    return db

def init_db():
    with closing(connect_db()) as db:
        with app.open_resource('database.schema', mode='r') as f:
            db.cursor().executescript(f.read())
        db.commit()

# This function takes one SQLite-query with some arguments (attributes)
# It returns a list of dictionaries for the results.
#
# E.g: A query can return 2 rows with 2 attributes:
# Result: [{'Att1': value1, 'Att2': value2}{'Att1': value3, 'Att2': value4}]
#
# Use dictlist[1]['Att2'] to get value4 for instance.
def query_db(query, args=()):
    db = None
    dictlist = None
    try:
        db = get_db()
        cursor = db.cursor()
        result = cursor.execute(query, args)

        # Fetch all rows with desired attributes from query
        data = result.fetchall()
        numberOfRows = len(data)
        if data:
            numberOfAttributes = len(result.description)

            # Create list of dictionaries and store queried rows in it
            dictlist = [dict() for x in range(numberOfRows)]
            for row in range(0, numberOfRows, 1):
                for column in range(0, numberOfAttributes, 1):
                    dictlist[row][result.description[column][0]] = data[row][column]
        else:
            print '# Query to database did not result in any received data.'
            db.commit()
            return None

    except:
        print "Exception: Unexpected error when querying database!"
        db.rollback()

    #finally:
        #db.close()

    return dictlist

def close():
    get_db().close()

# This function needs a dictionary with keys: "email", "password" and "token"
# "Password" is required and so is one of "email" and "token".
# It is possible to assign "None" to one of them.
def passwordIsCorrect(dict):
    email = dict['email']
    password = dict['password']
    token = dict['token']
    result = None
    if email != None and password != None:
        result = query_db('SELECT COUNT(email) AS count FROM Users WHERE email = ? AND password = ?', [email, password])
    elif token != None and password != None:
        result = query_db('SELECT COUNT(email) AS count FROM Users WHERE token = ? AND password = ?', [token, password])
    if result != None and result[0]['count'] > 0:
        return True
    else:
        return False

def signIn(email, password):
    if passwordIsCorrect(dict(email=email, password=password, token=None)):
        token = query_db('SELECT token FROM Users WHERE email = ?', [email])[0]['token']
        if not token:
            token = uuid.uuid4()
            #print generatedToken
            query_db('UPDATE Users SET token = ? WHERE email = ?', [str(token), email])

        return dict(success=True, message='Successfully signed in.', data=token) #result[0]['token'])
    else:
        return dict(success=False, message='Could not sign in.')

def setOnline(email):
    query_db('UPDATE Users SET online = ? WHERE email = ?', [1, email])
    return True

def setOffline(email):
    query_db('UPDATE Users SET online = ? WHERE email = ?', [0, email])
    return True

def signUp(email, password, firstname, lastname, gender, city, country):
    result = query_db('SELECT COUNT(email) AS count FROM Users WHERE email = ?', [email])
    #print result
    if result[0]['count'] == 0:
        if email != None and password != None and firstname != None and lastname != None and gender != '' and city != None and country != None:
            db = get_db()
            query_db('INSERT INTO Users (email, password) VALUES(?, ?)', [email, password])
            db.commit()
            query_db('INSERT INTO UserData VALUES(?, ?, ?, ?, ?, ?)', [email, firstname, lastname, gender, city, country])
            db.commit()
            return dict(success=True, message='Successfully created a new user.')
        else:
            return dict(success=False, message='Formdata not complete.')
    else:
        return dict(success=False, message='User already exists.')
    #db.close()

# Help-function
def isSignedIn(token):
    result = query_db('SELECT COUNT(token) AS count FROM Users WHERE token = ?', [token])
    if result[0]['count'] > 0:
        return True
    else:
        return False

def signOut(token):
    token = str(token)
    if isSignedIn(token):
        db = get_db()
        query_db('UPDATE Users SET token = NULL WHERE token = ?', [token])
        db.commit()
        return dict(success=True, message='Successfully signed out.')
    else:
        return dict(success=False, message='Your are not signed in.')

def changePassword(token, newPassword):
    token = str(token)
    db = get_db()
    query_db('UPDATE Users SET password = ? WHERE token = ?', [newPassword, token])
    db.commit()
    return True

def getUserData(dict):
    email = dict['email']
    token = dict['token']
    if email:
        result = query_db('SELECT * FROM UserData WHERE email = ?', [email])
        return result
    elif token:
        result = query_db('SELECT * FROM UserData WHERE email = (SELECT email FROM Users WHERE token = ?)', [token])
        return result

def getUserMessages(dict):
    email = dict['email']
    token = dict['token']
    result = None
    if email:
        result = query_db('SELECT sender, message, timestamp FROM Messages WHERE email = ?', [email])
    elif token:
        result = query_db('SELECT sender, message, timestamp FROM Messages WHERE email = (SELECT email FROM Users WHERE token = ?)', [token])

    return result

def postMessage(token, content, toEmail):
    token = str(token)

    sender = query_db('SELECT email FROM Users WHERE token = ?', [token])[0]['email']
    if not toEmail:
        toEmail = sender

    verifiedEmail = query_db('SELECT email FROM Users WHERE email = ?', [toEmail])
    if verifiedEmail:
        query_db('INSERT INTO Messages (email, sender, message) VALUES (?, ?, ?)', [toEmail, sender, content])
        return True
    else:
        return False

def increasePostsCount(token, email):
    if email:
        query_db('UPDATE Users SET posts = posts + 1 WHERE email = ?', [email])
        result = query_db('SELECT posts FROM Users WHERE email = ?', [email])[0]['posts']
    else:
        query_db('UPDATE Users SET posts = posts + 1 WHERE token = ?', [token])
        result = query_db('SELECT posts FROM Users WHERE token = ?', [token])[0]['posts']

    return result

def increaseVisitorsCount(email):
    query_db('UPDATE Users SET visitors = visitors + 1 WHERE email = ?', [email])
    result = query_db('SELECT visitors FROM Users WHERE email = ?', [email])[0]['visitors']
    return result

def getStats(token):
    countOnline = query_db('SELECT COUNT(*) AS count FROM Users WHERE online = ?', [1])
    countVisitorsPosts = query_db('SELECT visitors, posts FROM Users WHERE token = ?', [token])
    result = dict(online=countOnline[0]['count'],
                  visitors=countVisitorsPosts[0]['visitors'],
                  posts=countVisitorsPosts[0]['posts'])
    return result

def getTokenByEmail(email):
    # Return False if email is None
    if not email:
        return False
    token = query_db('SELECT token FROM Users WHERE email = ?', [email])[0]['token']
    # Return False if email has no token (user is not signed in)
    if not token:
        return False
    # Else, return token
    return token