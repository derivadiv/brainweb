import os, sys
sys.path.append("/home/gridsan/dpillai/sandbox") #replace with module location if it moves
import psql

# module for query translation?

def dbStats():
	schemas = psql.allSchemas()
	nestedresponse = {}
	for s in schemas:
		nestedresponse[s] = {}
		tables = psql.tablesInSchema(s)
		for t in tables:
			v = psql.countall(tablename=t, schemaname=s)
			nestedresponse[s][t] = v
	return nestedresponse
