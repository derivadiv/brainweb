# Starting simple HTTP server
import SimpleHTTPServer
import BaseHTTPServer
from routes import BrainHandler
import os, sys
sys.path.append(os.path.dirname(os.path.realpath(__file__)))

params = ('localhost',8000)

httpd = BaseHTTPServer.HTTPServer(params, BrainHandler)

print "serving at http://" + params[0] + ':' + str(params[1])
httpd.serve_forever()
# at http://localhost:8000
