import os
import sys
import psycopg2 # used to connect to PostGreSQL database
import psql # functions to connect to PostGreSQL database

hipfile = "/home/gridsan/groups/AF_Brains/images/Freesurfered/analysis_vol_hip_results.csv"
logfile = "/home/gridsan/groups/AF_Brains/images/Freesurfered/analysis_log_results.csv"

# Connect to database, setup of needed Freesurfer results schema/table(s)  *TODO: Move to SciDB
def dbstart():
	conn = psql.dbstart(schemaname="freesurfer")
	cur = conn.cursor()
	# Creates table 
	try:
		cur.execute("""CREATE TABLE IF NOT EXISTS freesurfer.log_files (
			Subject TEXT CONSTRAINT subkey PRIMARY KEY,
			Date TEXT,
			Version TEXT,
			Dicom TEXT,
			OrigLogFile TEXT
		);""")
	except:
		print 'Table (log_files) creation error'
		conn.rollback()

	try:
		cur.execute("""CREATE TABLE IF NOT EXISTS freesurfer.hip_vol (
			Subject TEXT CONSTRAINT subkey2 PRIMARY KEY,
			MRN TEXT,
			L_volume DECIMAL,
			R_volume DECIMAL,
			eTIV DECIMAL, 
			normL_volume DECIMAL, 
			normR_volume DECIMAL, 
			normTot_volume DECIMAL
		);""")
	except:
		print 'Table (hip_vol) creation error'
		conn.rollback()

	conn.commit()
	cur.close()
	return conn

# End connection
def dbend(conn):
	return psql.dbend(conn)

# freesurfer csv file insertion
def insert_fs_csv(conn, tname, filename):
	cur = conn.cursor()
	with open(filename, 'rb') as f:
		head = f.readline()
		cols = [x.replace(" ","").strip() for x in head.split(',')]
		for line in f:
			vals = [x.strip() for x in line.split(',')]
			if len(vals)==len(cols):
				# hippocampus table-specific fixes
				if 'hip_vol' in tname:
					# MRN should only include the number
					vals[1] = str.join('',[a for a in vals[1] if a.isdigit()])
					# columns after that must be numbers (decimal)- if not, replace with 0
					for v in range(2,len(vals)):
						try:
							vals[v] = float(vals[v][1:-1])
						except ValueError:
							vals[v] = 0
				# database insertion
				try:
					qstr = "INSERT INTO "+tname+" ("+", ".join(cols)+") VALUES ("+", ".join(['%s']*len(vals))+")"
					cur.execute(qstr,vals)
					conn.commit()
				except:
					print 'Insertion into '+tname+' didn\'t work on '+vals[0]
					conn.rollback()

		f.close()

	# save db operations
	conn.commit()
	cur.close()
	return


# insert freesurfer log file data into database
if __name__=='__main__':
	if len(sys.argv) == 1 :
		conn = dbstart()
		insert_fs_csv(conn, "log_files", logfile)
		insert_fs_csv(conn, "hip_vol", hipfile)
		dbend(conn)
	elif len(sys.argv) == 3:
		conn = dbstart()
		insert_fs_csv(conn, "log_files", sys.argv[1])
		insert_fs_csv(conn, "hip_vol", sys.argv[2])
		dbend(conn)
	else:
		print 'Usage: python fs_sql.py <CSV_File_Path_Hip_Vols> <CSV_File_Path_Log_Vols>, or just python fs_sql.py to use automatic ones'