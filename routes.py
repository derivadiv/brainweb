# Handling routes
import SimpleHTTPServer
import json
try:
	import queries
except:
	queries=None

Handler = SimpleHTTPServer.SimpleHTTPRequestHandler # module not instance


class BrainHandler(Handler):
	# overriding POST method? because js router is handling GET requests...
	def do_POST(self):
		if self.path == '/testme':
			# get database query?
			if queries:
				c = queries.dbStats()
				res = {'data':c}
			else:
				res = {'data':{'schema1':{'table1':200,'table2':300},'schema2':{'table3': 400}}}
			self.wfile.write(json.dumps(res))
