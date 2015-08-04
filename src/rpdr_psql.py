import os
import sys
import datetime # to fix RPDR dates
import psycopg2 # used to connect to PostGreSQL database
import psql # functions to connect to PostGreSQL database

# Connect to database, path to RPDR schema
def dbstart():
	conn = psql.dbstart(schemaname="rpdr")
	return conn

# End connection
def dbend(conn):
	return psql.dbend(conn)

# RPDR (only testing on demographics) txt file insertion
def insert_rpdr_txt(conn, tname, filename):
	cur = conn.cursor()
	with open(filename, 'rb') as f:
		head = f.readline()
		cols = [x.replace(" ","").strip().lower() for x in head.split('|')]
		datecols = [i for i in range(len(cols)) if 'date' in cols[i]]
		for line in f:
			vals = [x.strip() for x in line.split('|')]
			for i in datecols:
				try:
					vals[i] = datetime.datetime.strptime(vals[i], '%m/%d/%Y')
				except ValueError:
					vals[i] = None #what else to do with missing dates? missing death date should be allowed
			if len(vals)==len(cols):
				# database insertion
				try:
					qstr = "INSERT INTO "+tname+" ("+", ".join(cols)+") VALUES ("+", ".join(['%s']*len(vals))+")"
					cur.execute(qstr, vals)
					conn.commit()
				except:
					print 'Insertion into '+tname+' didn\'t work on '+vals[0]
					conn.rollback()

		f.close()

	# save db operations
	conn.commit()
	cur.close()
	return


# insert RPDR data into database table
if __name__=='__main__':
	if len(sys.argv) == 3 :
		conn = dbstart()
		insert_rpdr_txt(conn, sys.argv[1], sys.argv[2])
		dbend(conn)
	else:
		print 'Usage: python rpdr_psql.py <RPDRTableName> <PathToRPDRTxtFile>'