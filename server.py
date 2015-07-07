# Starting simple HTTP server, code from https://docs.python.org/2/library/simplehttpserver.html

import SimpleHTTPServer
import SocketServer

PORT = 8000

Handler = SimpleHTTPServer.SimpleHTTPRequestHandler

httpd = SocketServer.TCPServer(("", PORT), Handler)

print "serving at port", PORT
httpd.serve_forever()
# at http://127.0.0.1:8000