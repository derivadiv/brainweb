# module for query translation, intermediate between backend database calls and website routes
try: 
	import psql
except:
	psql = None # for working/ testing locally outside SuperCloud
import scidb

def dbStats(numtries = 2):
	conn = None
	if psql:
		while conn is None and numtries > 0:
			conn = psql.dbstart()
			numtries = numtries - 1
		if conn:
			schemas = psql.allSchemas(conn)
			nestedresponse = {}
			for s in schemas:
				nestedresponse[s] = {}
				tables = psql.tablesInSchema(conn, s)
				for t in tables:
					v = psql.countall(conn, t, schemaname=s)
					nestedresponse[s][t] = v
			psql.dbend(conn)
			return nestedresponse
	return {'data':{'schema1':{'table1':200,'table2':300},'schema2':{'table3': 400}}}

def hipVols(numtries = 2):
	conn = None
	if psql:
		while conn is None and numtries > 0:
			conn = psql.dbstart()
			numtries = numtries - 1
		if conn:
			# freesurfer hip_vol is now in scidb target, try that first, otherwise can load from postgres
			cols = ['Subject', 'MRN', 'normTot_volume']
			fhiprows = scidb.selectDB(toselect=','.join([c.lower() for c in cols]))
			# cols = ['Subject', 'MRN', 'normTot_volume']
			# fhiprows = psql.selectDB(conn, ['Subject', 'MRN', 'normTot_volume'], "hip_vol", "freesurfer")
			# adding date and dicom file name?
			cols.extend(['Date','Dicom'])
			oldrows = fhiprows
			newrows = []
			for row in oldrows:
				subject = row[0]
				row = list(row)
				qrows = psql.selectDB(conn,['Date','Dicom'],"log_files","freesurfer",whereclause="Subject = %s"%subject)
				if qrows is not None and len(qrows) > 0:
					row.extend(list(qrows[0]))
				else:
					row.extend(['',''])
				newrows.append(row)
			# adding birthdate from rpdr
			cols.extend(['Date_of_Birth'])
			oldrows = newrows
			newrows = []
			for row in oldrows:
				row[1] = str.join('',[a for a in row[1] if a.isdigit()])
				mrn = row[1]
				qrows = psql.selectDB(conn,['Date_of_Birth'],"Dem","rpdr",whereclause="MRN = '%s'"%mrn)
				if qrows is not None and len(qrows) > 0:
					val = str(qrows[0][0])
					row.append(val)
				else:
					row.append('')
				newrows.append(row)
			# adding DICOM information? how about seriesdescription, protocolname, and patientage?
			cols.extend(['SeriesDescription','ProtocolName','PatientAge'])
			oldrows = newrows
			newrows = []
			for row in oldrows:
				# many extra things in stored dicom paths: just keep the last part, raw filename?
				dicom = row[4].split('/')[-1]
				qrows = psql.selectDB(conn,['SeriesDescription','ProtocolName','PatientAge'],"imagemeta","dicom",whereclause="FilePath LIKE '%"+str(dicom)+"'")
				if qrows is not None and len(qrows) > 0:
					row.extend(list(qrows[0]))
				else:
					row.extend(['','',''])
				newrows.append(row)

			psql.dbend(conn)
			newrows = [cols] + newrows
			return newrows
	# otherwise, fake test data can be returned?
	return [['Subject', 'MRN', 'normTot_volume','Date','Dicom','Date_of_Birth','SeriesDescription','ProtocolName','PatientAge'],['subj###', '###', 0.12,'DateTime1','FilePath','DateTime2','Series','T1Weighted',18]];