# Starting simple HTTP server
import SimpleHTTPServer
import BaseHTTPServer
from routes import BrainHandler

params = ('localhost',8000)

httpd = BaseHTTPServer.HTTPServer(params, BrainHandler)

print "serving at port ", params[1]
httpd.serve_forever()
# at http://localhost:8000
