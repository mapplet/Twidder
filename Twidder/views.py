from Twidder import app
from flask import request, json
import database_helper

connectionsByToken = {}
connectionsByWS = {}

@app.route('/socket_connect', methods=['GET'])
def socketConnect():
    if request.method == 'GET':
        if request.environ.get('wsgi.websocket'):
            print '# Incoming socketConnect'
            WebSocket = request.environ['wsgi.websocket']

            while True:
                receivedData = WebSocket.receive()
                if not receivedData:
                    # Connection is closed.
                    break

                if connectionsByToken.get(receivedData, False):
                    print '# Will close first connection.'
                    expiredWebSocket = connectionsByToken[receivedData]
                    del connectionsByToken[receivedData]
                    del connectionsByWS[expiredWebSocket]
                    expiredWebSocket.close()

                print '# Will add connection.'
                connectionsByToken[receivedData] = WebSocket
                connectionsByWS[WebSocket] = receivedData
                print '#(1-TO) Connections: ' + str(connectionsByToken)
                print '#(1-WS) Connections: ' + str(connectionsByWS)
                for connection in connectionsByWS:
                    connection.send('user signed in')

            if connectionsByWS.get(WebSocket, False):
                print '# User signed out.'
                expiredToken = connectionsByWS[WebSocket]
                del connectionsByToken[expiredToken]
                del connectionsByWS[WebSocket]
            WebSocket.close()
            print '#(2-TO) Connections: ' + str(connectionsByToken)
            print '#(2-WS) Connections: ' + str(connectionsByWS)
            for connection in connectionsByWS:
                    connection.send('user signed out')

        return 'socketDisconnect'

@app.route('/', methods=['GET'])
def welcome():
    if request.method == 'GET':
        return app.send_static_file('client.html')
        # return render_template('client.html')

@app.route('/sign_in', methods=['POST'])
def signIn():
    if request.method == 'POST':
        email = request.form['email']
        password = request.form['password']

        if email and email != '' \
            and password and password != '':
            result = database_helper.signIn(email, password)
        else:
            result = {'success':False}

        if result['success'] == True:
            database_helper.setOnline(email)
            data = {'success':True, 'message':'Successfully signed in.', 'data':result['data']}
            return json.dumps(data, sort_keys = True, indent = 2)
        else:
            data = {'success':False, 'message':'Wrong username or password.'}
            return json.dumps(data, sort_keys = True, indent = 2)

@app.route('/sign_up', methods=['POST'])
def signUp():
    if request.method == 'POST':
        firstname = request.form['firstname']
        lastname = request.form['lastname']
        gender = request.form['gender']
        city = request.form['city']
        country = request.form['country']
        email = request.form['email']
        password = request.form['password']
        #print 'HaR: ' + firstname + ' ' + lastname + ' ' + gender + ' ' + city + ' ' + country + ' ' + email + ' ' + password
        if firstname and firstname != '' \
                and lastname and lastname != '' \
                and gender and gender != '' \
                and city and city != '' \
                and country and country != '' \
                and email and email != '' \
                and password and password != '':
            result = database_helper.signUp(email, password, firstname, lastname, gender, city, country)
        else:
            result = {'success':False, 'message':'Unvalid formdata.'}

        return json.dumps(result, sort_keys = True, indent = 2)

@app.route('/sign_out', methods=['POST'])
def signOut():
    if request.method == 'POST':
        # Hardcoded token request
        token = request.form['token']
        userData = database_helper.getUserData(dict(email=None, token=token))
        email = userData[0]['email']
        if token and token != '':
            result = database_helper.signOut(token)
        else:
            result = {'success':False}

        if result['success'] == True:
            database_helper.setOffline(email)
            data = {'success':True, 'message':'Successfully signed out'}
            return json.dumps(data, sort_keys = True, indent = 2)
        else:
            data = {'success':False, 'message':'You are not signed in.'}
            return json.dumps(data, sort_keys = True, indent = 2)

@app.route('/change_password', methods=['POST'])
def changePassword():
    if request.method == 'POST':
        # Hardcoded token request
        token = request.form['token']
        oldPassword = request.form['oldPassword']
        newPassword = request.form['newPassword']

        if token and token != '' \
            and oldPassword and oldPassword != '' \
            and newPassword and newPassword != '' \
            and oldPassword != newPassword:

            if database_helper.isSignedIn(token):
                if database_helper.passwordIsCorrect(dict(email=None, password=oldPassword, token=token)):
                    database_helper.changePassword(token, newPassword)
                    data = {'success':True, 'message':'Password changed.'}
                    return json.dumps(data, sort_keys = True, indent = 2)
                else:
                    data = {'success':False, 'message':'Wrong password.'}
                    return json.dumps(data, sort_keys = True, indent = 2)
            else:
                data = {'success':False, 'message':'You are not signed in.'}
                return json.dumps(data, sort_keys = True, indent = 2)
        else:
            data = {'success':False, 'message':'Passwords are identical.'}
            return json.dumps(data, sort_keys = True, indent = 2)

@app.route('/get_user_data/<email>', methods=['POST'])
@app.route('/get_user_data', methods=['POST'])
def getUserData(email=None):
    if request.method == 'POST':
        # Hardcoded token request
        token = request.form['token']
        if database_helper.isSignedIn(token):
            if email:
                userData = database_helper.getUserData(dict(email=email, token=None))
            else:
                userData = database_helper.getUserData(dict(email=None, token=token))
            if userData:
                data = {'success':True, 'message':'User data retrieved.', 'data':userData[0]}
                return json.dumps(data, sort_keys = True, indent = 2)
            else:
                data = {'success':False, 'message':'No such user.'}
                return json.dumps(data, sort_keys = True, indent = 2)
        else:
            data = {'success':False, 'message':'You are not signed in.'}
            return json.dumps(data, sort_keys = True, indent = 2)

@app.route('/post_message', methods=['POST'])
def postMessage():
    if request.method == 'POST':
        # Hardcoded token request
        token = request.form['token']
        if database_helper.isSignedIn(token):
            toEmail = None
            try:
                toEmail = request.form['toEmail']
            except:
                print '# No toEmail: Post on my wall'

            content = request.form['content']
            result = database_helper.postMessage(token, content, toEmail)
            if result:
                database_helper.increasePostsCount(token, toEmail)
                data = {'success':True, 'message':'Message posted.'}

                tokenOfRecipient = database_helper.getTokenByEmail(toEmail)
                if not toEmail:
                    # We wrote on our own wall
                    connectionsByToken[token].send('new post')
                elif tokenOfRecipient:
                    if tokenOfRecipient in connectionsByToken:
                        connectionsByToken[tokenOfRecipient].send('new post')

                return json.dumps(data, sort_keys = True, indent = 2)
            else:
                data = {'success':False, 'message':'No such user.'}
                return json.dumps(data, sort_keys = True, indent = 2)
        else:
            data = {'success':False, 'message':'You are not signed in.'}
            return json.dumps(data, sort_keys = True, indent = 2)

@app.route('/get_user_messages/<email>', methods=['POST'])
@app.route('/get_user_messages', methods=['POST'])
def getUserMessages(email=None):
    if request.method == 'POST':
        # Hardcoded token request
        token = request.form['token']
        if database_helper.isSignedIn(token):
            if email:
                userMessages = database_helper.getUserMessages(dict(email=email, token=None))
            else:
                userMessages = database_helper.getUserMessages(dict(email=None, token=token))
            if userMessages:
                data = {'success':True, 'message':'User messages retrieved.', 'data':userMessages}
                return json.dumps(data, sort_keys = True, indent = 2)
            else:
                data = {'success':False, 'message':'No messages to retrieve.'}
                return json.dumps(data, sort_keys = True, indent = 2)
        else:
            data = {'success':False, 'message':'You are not signed in.'}
            return json.dumps(data, sort_keys = True, indent = 2)

@app.route('/get_stats', methods=['POST'])
def getStats():
    # Hardcoded token request
    token = request.form['token']
    stats = None
    if token and token != '':
        stats = database_helper.getStats(token)

    if stats:
        data = {'success':True, 'message':'Stats retrieved.', 'data':stats}
        return json.dumps(data, sort_keys = True, indent = 2)
    else:
        data = {'success':False, 'message':'You are not signed in.'}
        return json.dumps(data, sort_keys = True, indent = 2)

@app.route('/increase_visitor_count', methods=['POST'])
def increaseVisitorCount():
    email = request.form['email']
    result = database_helper.increaseVisitorsCount(email)

    tokenOfRecipient = database_helper.getTokenByEmail(email)
    if tokenOfRecipient in connectionsByToken:
        connectionsByToken[tokenOfRecipient].send('new visitor')

    return str(result)