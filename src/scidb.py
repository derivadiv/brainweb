import subprocess

def selectDB(toselect="*", whereclause=None):
	query = "SELECT "+toselect+" FROM target "
	if whereclause:
		query += "WHERE "+whereclause
	args = ['iquery', '-q '+query]
	out = subprocess.check_output(args)
	lines = [x[x.index('}')+2:]  for x in out.split('\n')[:-1]]
	vals = [l.split(',') for l in lines[1:]]
	return vals