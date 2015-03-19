from geventwebsocket.handler import WebSocketHandler
from gevent.pywsgi import WSGIServer
from Twidder import app
from werkzeug.serving import run_with_reloader
# app.run(debug=True)

@run_with_reloader
def run_server():
    app.debug = True
    http_server = WSGIServer(('',5000), app, handler_class=WebSocketHandler)
    http_server.serve_forever()

if __name__ == '__main__':
    run_server()