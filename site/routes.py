# Handling routes
import SimpleHTTPServer
import json
import queries

Handler = SimpleHTTPServer.SimpleHTTPRequestHandler # module not instance


class BrainHandler(Handler):
	# overriding POST method? because js router is handling GET requests...
	def do_POST(self):
		if self.path == '/testme':
			# get database query?
			c = queries.dbStats()
			res = {'data':c}
			self.wfile.write(json.dumps(res))
		elif self.path == '/hippovol': 
			c = queries.hipVols()
			res = {'data':c}
			print c
			self.wfile.write(json.dumps(res))
