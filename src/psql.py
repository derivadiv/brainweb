# used to connect to PostGreSQL database
import psycopg2 
# database params stored in config.connectstr
from config import connectstr 

# fixing Decimal types?
DEC2FLOAT = psycopg2.extensions.new_type(
    psycopg2.extensions.DECIMAL.values,
    'DEC2FLOAT',
    lambda value, curs: float(value) if value is not None else None)
psycopg2.extensions.register_type(DEC2FLOAT)

# Connect to database, setup of needed schema/table(s)
def dbstart(schemaname=None, tablename=None, coltags=[], connectstr=connectstr):
    try:
        conn = psycopg2.connect(connectstr)
    except: 
        print "Can't connect"
        return    

    if schemaname:
        createSchema(conn, schemaname)
        
    if tablename:
        createTable(conn, tablename, coltags, schemaname)

    return conn

def createSchema(conn, schemaname):
    cur = conn.cursor()
    try:
        cur.execute("CREATE SCHEMA IF NOT EXISTS " + schemaname + ";")
        cur.execute("SET search_path TO " + schemaname + ";")
        conn.commit()
        cur.close()
        return True
    except:
        print 'Schema error'
        conn.rollback()
        cur.close()
    return

# Creates table in current/default schema, whatever that is
def createTable(conn, tablename, coltags=[], schemaname = None):
    cur = conn.cursor()
    try:
        qstr = "CREATE TABLE IF NOT EXISTS "
        if schemaname:
            qstr = qstr + schemaname + '.'
        qstr = qstr + tablename + "(" + ', '.join([x[0]+' '+x[1] for x in coltags]) + ");"
        cur.execute(qstr)
        conn.commit()
        cur.close()
        return True
    except:
        print 'Table creation error'
        conn.rollback()
        cur.close()
    return

def dbend(conn):
    # fix search_path, set to default only look in public schema unless qualified?
    conn.rollback()
    cur = conn.cursor()
    cur.execute("SET search_path TO public;")
    conn.commit() # in case forgotten elsewhere
    cur.close()
    conn.close()
    return

def insert_dict(conn, savedict, tablename):
    cur = conn.cursor()
    try:
        cols = savedict.keys()
        v = ", ".join(["'" + savedict[cols[i]] + "'" for i in range(len(cols))])
        c = ", ".join(cols)
        qstr = "INSERT INTO " + tablename + " ( " + c + ") VALUES (" + v + ");"
        # print qstr
        cur.execute(qstr) 
    except:
        print 'Desired insertion didn\'t work'
        conn.rollback()
        cur.close()
        return
    # Save db operation
    conn.commit()
    cur.close()
    return

def countall(conn, tablename, schemaname=None):
    cur = conn.cursor()
    qstr = "SELECT COUNT(*) FROM "
    if schemaname:
        qstr = qstr + schemaname + "."
    qstr = qstr + tablename + ";"
    rows = []
    try:
        cur.execute(qstr)
        rows = cur.fetchall()
    except:
        print 'Select didn\'t work'
    if len(rows) == 1:
        return rows[0][0]
    return '?'

def allSchemas(conn):
    cur = conn.cursor()
    qstr = "SELECT schema_name FROM information_schema.schemata;"
    try:
        cur.execute(qstr)
        rows = cur.fetchall()
    except:
        print 'Select (schemas) didn\'t work'
        conn.rollback()
        rows = []
    return [r[0] for r in rows]

def tablesInSchema(conn, schemaname):
    cur = conn.cursor()
    qstr = "SELECT table_name FROM information_schema.tables WHERE table_type=\'BASE TABLE\' AND table_schema=\'" + schemaname + "\';" 
    try:
        cur.execute(qstr)
        rows = cur.fetchall()
    except:
        print 'Select (tables) didn\'t work'
        conn.rollback()
        rows = []
    return [r[0] for r in rows]

def selectDB(conn, cols, table, schema, whereclause=None):
    cur = conn.cursor()
    qstr = "SELECT "+", ".join(cols)+" FROM "+schema+'.'+table
    if whereclause:
        qstr = qstr + " WHERE " + whereclause
    qstr = qstr + ";"
    try:
        cur.execute(qstr)
        rows = cur.fetchall()
    except:
        print 'Custom select didn\'t work'
        conn.rollback()
        return
    return [r[:len(cols)] for r in rows]