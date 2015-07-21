# rpdr.py - nareynolds, edited for postgres

# add working directory to search path
import os
import sys
sys.path.insert(0, os.path.realpath(__file__))
# path added for location of psql (database query) files, can edit if it changes
sys.path.append(os.path.dirname(os.getcwd()))

# get RPDR Table info
import rpdrdefs

# get file management tools
import shutil
import fnmatch
import re

# Switching from sqlite to postgres
import psql

# get csv tools
import csv

# get time tools
import time

# for dealing with unicode
import unicodedata



class Dataset:

    #--------------------------------------------------------------------------------------------
    # instantiation
    def __init__ ( self, dataDir, dbName='RPDR_DATASET' ):

        # save directory
        self.dir = dataDir

        # compute path to SQLite database
        # self.dbPath = os.path.join( self.dir, '%s.sqlite' % dbName )

        # search for RPDR text files
        self.tables = self.findTables(self.dir)
        if len(self.tables) < 1:
            print "Warning! No RPDR files found in given directory: %s" % self.dir
            
            # search for SQLite database
        #     if not os.path.isfile(self.dbPath):
        #         print "Warning! SQLite database found: %s" % self.dbPath
        #         return

        # # create/connect to SQLite database and enable dictionary access of rows
        # if not os.path.isfile(self.dbPath):
        #     print "Creating SQLite database: %s" % self.dbPath


        # sometimes multiple connection attempts are required for psql, not sure why
        self.dbCon = None;
        nTries = 3
        n = nTries
        while n > 0 and self.dbCon is None:
            self.dbCon = psql.dbstart(schemaname = "rpdr")
            n -= 1

        if self.dbCon is None:
            print "Failed to connect in %s tries" % nTries
            return
        print "Connected, will read from %s" % self.dir

        #self.dbCon.row_factory = sqlite3.Row

        # loop through RPDR text files
        for tableName in self.tables:

            if not self.dbExistsRpdrTable( tableName ):
                # create RPDR table in database
                self.dbCreateRpdrTable( tableName )

            if self.dbExistsRpdrTable( tableName ):
                # fill table
                self.dbFillRpdrTable( tableName )

            # count check
            count = self.dbCountRpdrTable( tableName )
            print "%s rows in table %s" % (count, tableName)
            if count > 0:
                self.dbCon.commit()


    #--------------------------------------------------------------------------------------------
    # 
    def findTables ( self, dataDir ):

        # check that the given directory exists
        if not os.path.isdir(dataDir):
            print "Error! Given directory doesn't exist: %s" % dataDir
            return

        # list the import directory files
        files = [ f for f in os.listdir(dataDir) if os.path.isfile( os.path.join(dataDir,f) ) ]

        # get list of vaild RPDR file endings
        rpdrFileEndings = [ '%s.%s' % (table.name, table.fileExt) for table in rpdrdefs.Tables]

        # check if each file follows the RPDR naming convention
        rpdrFiles = []
        rpdrFilePrefixes = []
        for f in files:
            for fileEnding in rpdrFileEndings:
                if f.endswith( fileEnding ):
                    rpdrFiles.append(f)
                    rpdrFilePrefixes.append( f.rstrip(fileEnding) )
                    break

        # check if all RPDR files have the same prefix
        if len(list(set( rpdrFilePrefixes ))) > 1:
            print "Warning! Not all the RPDR files have the same prefix: %s" % str(rpdrFilePrefixes)

        # loop through RPDR files
        tables = {}
        for rpdrFile in rpdrFiles:
            filePath = os.path.join( dataDir, rpdrFile )

            # determine type of RPDR table of the file
            tableDefinition = None
            for t in rpdrdefs.Tables:
                if filePath.endswith( '%s.%s' % (t.name, t.fileExt) ):
                    tableDefinition = t
                    break

            # check that file is a known RPDR table type
            if tableDefinition == None:
                print "Error! File is not a known RPDR file: %s" % filePath
                return

            # open file as csv file with approriate dialect
            csvFile = open(filePath,"rU")
            csvReader = csv.reader(
                csvFile,
                delimiter = tableDefinition.csvDialect.delimiter,
                doublequote = tableDefinition.csvDialect.doublequote,
                escapechar = tableDefinition.csvDialect.escapechar,
                lineterminator = tableDefinition.csvDialect.lineterminator,
                quotechar = tableDefinition.csvDialect.quotechar,
                quoting = tableDefinition.csvDialect.quoting,
                skipinitialspace = tableDefinition.csvDialect.skipinitialspace,
                strict = tableDefinition.csvDialect.strict
            )

            # get CSV headers from file
            headers = csvReader.next()

            # close file
            csvFile.close()

            # check headers against table definitions in RpdrTables
            columns = [ col.name for col in tableDefinition.columns ]
            unexpectedCols = []
            for header in headers:
                if header.strip() not in columns:
                    unexpectedCols.append( header )

            if len(unexpectedCols) > 0:
                print "Error! Unexpected columns found in %s.txt: %s" % ( tableDefinition.name, str(unexpectedCols) )
                return

            if len(columns) > len(headers):
                print "Error! Missing columns in file %s.txt: %s" % ( tableDefinition.name, list(set(columns) - set(headers)) ) 
                return

            tables[tableDefinition.name] = { 'file':filePath, 'definition':tableDefinition }

        #
        return tables

    
    #--------------------------------------------------------------------------------------------
    # 
    # returns true if table with this name exists in rpdr schema
    def dbExistsRpdrTable (self, tableName ):
        tableDefinition = self.tables[tableName]['definition']

        # check if the RPDR table already exists
        with self.dbCon:
            dbCur = self.dbCon.cursor()
            dbCur.execute( "SELECT table_name FROM information_schema.tables WHERE table_type=\'BASE TABLE\' AND table_schema=\'rpdr\' AND table_name='%s'" % tableDefinition.name.lower() )
            qResult = dbCur.fetchone()
            if (qResult is not None):
                return True
        return

    # get row count of RPDR table
    def dbCountRpdrTable (self, tableName) :
        tableDefinition = self.tables[tableName]['definition']

        with self.dbCon:
            dbCur = self.dbCon.cursor()
            dbCur.execute( "SELECT count(*) from rpdr.%s" % tableDefinition.name.lower() )
            qResult = dbCur.fetchone()
            if (qResult is not None):
                return qResult[0]
        return

    # Edited: does not ensure that table exists beforehand (see dbExistsRpdrTable)
    def dbCreateRpdrTable ( self, tableName ):
        # create column declarations
        colDecs = []
        for col in tableDefinition.columns:
            newDec = " %s %s " % (col.name, col.type)
            # dealing with keywords
            if col.name == 'Group':
                newDec = " %s %s " % ('GroupText', col.type)
            if col.notNull:
                newDec = " %s NOT NULL " % newDec
            if col.primaryKey:
                newDec = " %s PRIMARY KEY " % newDec

            colDecs.append( newDec )

            # shouldn't use unique with "INSERT OR IGNORE" below to avoid unexpected ignoring of data
            # not including foreign keys, because not worth the work.
            #if col.unique:
            #    newDec = " %s UNIQUE " % newDec

        # create database table
        qCreate = "CREATE TABLE %s ( %s )" % ( tableDefinition.name, ','.join(colDecs) )
        with self.dbCon:
            dbCur = self.dbCon.cursor()
            print "Creating database table: %s" % tableDefinition.name
            dbCur.execute(qCreate)
            self.dbCon.commit()
            dbCur.close()

        # add column indices
        for col in tableDefinition.columns:
            if col.index:
                with self.dbCon:
                    dbCur = self.dbCon.cursor()
                    qIndex = "CREATE INDEX %s_%s_idx ON %s (%s)" % (tableDefinition.name, col.name, tableDefinition.name, col.name)
                    dbCur.execute(qIndex)
                    self.dbCon.commit()
                    dbCur.close()

        #
        return True



    #--------------------------------------------------------------------------------------------
    # 
    def dbFillRpdrTable ( self, tableName ):
        tableDefinition = self.tables[tableName]['definition']
        filePath = self.tables[tableName]['file']

        # get list of column names in table
        columnNames = [ col.name for col in tableDefinition.columns ]
        if 'Group' in columnNames:
            i = columnNames.index('Group')
            columnNames[i] = 'GroupText'

        # prepare insert query - will ignore duplicates for tables with primary keys and uniqueness
        qInsert = "INSERT INTO %s ( %s ) VALUES ( %s )" % (tableDefinition.name, ', '.join(columnNames), ', '.join([ '\'%s\'' for col in columnNames]) )
        
        # header table definitions from RpdrTables
        # columnNames = [ col.name for col in tableDefinition.columns ]

        # open file as csv file with approriate dialect
        csvFile = open(filePath,"rU")
        csvReader = csv.reader(
            csvFile,
            delimiter = tableDefinition.csvDialect.delimiter,
            doublequote = tableDefinition.csvDialect.doublequote,
            escapechar = tableDefinition.csvDialect.escapechar,
            lineterminator = tableDefinition.csvDialect.lineterminator,
            quotechar = tableDefinition.csvDialect.quotechar,
            quoting = tableDefinition.csvDialect.quoting,
            skipinitialspace = tableDefinition.csvDialect.skipinitialspace,
            strict = tableDefinition.csvDialect.strict
        )

        # get CSV headers from file
        headers = csvReader.next()

        # fill table
        print "Filling database table: '%s'" % tableDefinition.name
        with self.dbCon:
            dbCur = self.dbCon.cursor()
            numCols = len(columnNames)
            lineIdx = -1
            for rIdx, row in enumerate(csvReader):
                lineIdx = lineIdx + 1
                try:

                    # check for too few columns
                    if len(row) < numCols:
                        print "Error (row %d)! Less than %d columns found! %s" % (lineIdx, numCols, row)
                        # return # move on
                        break
                    # handle extra columns: combine end columns
                    if len(row) > numCols:
                        row = row[:numCols-1] + ['|'.join(row[numCols-1:])]
                    # reformatting
                    for cIdx, col in enumerate(tableDefinition.columns):

                        # enforce ascii text
                        if row[cIdx]:
                            row[cIdx] = self.enforce_ascii( row[cIdx] )

                        # date reformatting
                        if col.dateReformat and row[cIdx]:
                            row[cIdx] = time.strftime( col.dateReformat.reformat, time.strptime(row[cIdx], col.dateReformat.format) )
                    # handle free-text report in last column
                    if tableDefinition.freeTextReportInLastColumn:
                        reportRows = [ row[-1] ]
                        while 1:
                            nextRow = csvReader.next()
                            lineIdx = lineIdx + 1
                            if not nextRow:
                                reportRows.append('')
                            else:
                                if '[report_end]' not in nextRow[0]:
                                    reportRows.append( '|'.join(nextRow) )
                                else:
                                    break
                        row[-1] = '\n'.join(reportRows)
                    # insert row into database
                    try:
                        dbCur.execute(qInsert % tuple(row))
                        self.dbCon.commit()
                    except:
                        self.dbCon.rollback()

                except:
                    print "Error processing line %d:" % lineIdx
                    # raise 
                    # instead, skip that line and move on
            dbCur.close()
        # close file
        csvFile.close()



    #--------------------------------------------------------------------------------------------
    def enforce_ascii(self, s):

        # strip non-unicode characters
        s = "".join(i for i in s if ord(i)<128)

        # ascii encoding
        s = s.encode('ascii','ignore')

        return s




class Patient:

    #--------------------------------------------------------------------------------------------
    def __init__( self, dataset, empi=None ):
    
        # validate args
        if dataset is None:
            print "Warning! Must provide RPDR dataset"
            return
        if empi is None:
            print "Warning! Must provide patient EMPI"
            return
        
        # RPDR dataset
        self.dataset = dataset

        # database info
        self.dbPath = self.dataset.dbPath
        self.dbCon = self.dataset.dbCon

        # patient Enterprise Master Patient Index (EMPI)
        self.empi = empi

        # names of RPDR tables
        self.rpdrTableNames = [ t.name for t in rpdrdefs.Tables ]

        # given RPDR dataset table names
        self.datasetTableNames = None

        # given RPDR dataset table definitions
        self.datasetTableDefinitions = None

        # given RPDR dataset table names used in self.timeline()
        self.timelineTableNames = None

        # given RPDR dataset table definitions used in self.timeline()
        self.timelineTableDefinitions = None

        # basic info about patient
        self.demographics = None

        # notes about the patient saved in database
        self.patientNotes = None


        # get list of tables in database
        with self.dbCon:
            dbCur = self.dbCon.cursor()
            dbCur.execute( "SELECT table_name FROM information_schema.tables WHERE table_type=\'BASE TABLE\' AND table_schema=\'rpdr\'" )
            qResult = dbCur.fetchall()
            if (qResult is None) or (len(qResult) == 0):
                print "Warning! No tables in database."
                return
            else:
                dbTableNames = [str(row[0]) for row in qResult]
    
        # get list of RPDR tables in given database
        self.datasetTableNames = [ n for n in dbTableNames if n in self.rpdrTableNames ]
        self.datasetTableDefinitions = [ t for t in rpdrdefs.Tables if t.name in self.datasetTableNames ]
        
        # check that there are rpdr tables in given database
        if len(self.datasetTableNames) < 1:
            print "Warning! No RPDR tables found in database."
            
        # get list of RPDR tables in database to use in self.timeline()
        possibleTimelineTableNames = [ t.name for t in rpdrdefs.Tables if t.useInTimeline ]
        self.timelineTableNames = [ n for n in dbTableNames if n in possibleTimelineTableNames ]
        self.timelineTableDefinitions = [ t for t in rpdrdefs.Tables if t.name in self.timelineTableNames ]

        # search for basic patient demographics
        with self.dbCon:
            dbCur = self.dbCon.cursor()
            dbCur.execute( "SELECT * FROM Dem WHERE EMPI=? LIMIT 1", (empi,) )
            qResult = dbCur.fetchone()
            if qResult is None:
                print "Warning: Couldn't find patient in Dem with EMPI = %s." % empi
                return
            self.demographics = qResult
        
        # instantiate PatientNotes to use with this patient
        self.patientNotes = PatientNotes(self.dataset)



    #--------------------------------------------------------------------------------------------
    def timeline( self, tables='' ):

        # determine tables to search
        if tables:
            timelineTableDefinitions = [ t for t in self.timelineTableDefinitions if t.name in tables ]
            if not timelineTableDefinitions:
                print "Error: Provided timeline tables are invalid ( %s )" % tables
                return
        else:
            timelineTableDefinitions = self.timelineTableDefinitions
        
        # create SQL search query
        tablesSearchQueries = []
        for tableDefinition in timelineTableDefinitions:
            dateColName = None
            blurbColName = None
            for col in tableDefinition.columns:
                if col.timelineDate:
                    dateColName = col.name
                if col.timelineBlurb:
                    blurbColName = col.name
            q = "SELECT '%s' AS 'Table', rowid AS EventId, %s AS Date, round( ( ( julianday(%s) - julianday('%s') ) / 365 ), 2 ) AS Age, %s AS Blurb FROM %s WHERE EMPI = %s" \
                % (tableDefinition.name, dateColName, dateColName, self.demographics['Date_of_Birth'], blurbColName, tableDefinition.name, self.empi )
            tablesSearchQueries.append(q)
        qSearch = "Select * From ( %s ) ORDER BY Date" % " UNION ".join(tablesSearchQueries)

        # query database
        events = None
        with self.dbCon:
            dbCur = self.dbCon.cursor()
            dbCur.execute( qSearch )
            qResult = dbCur.fetchall()
            if (qResult is None) or (len(qResult) == 0):
                print "Warning! Database query returned nothing."
                return
            events = qResult

        # print events
        print " _______________________________________________________________________________________________\n |"
        print " | Timeline: %s" % str(tables)
        print " |----------------------------------------------------------------------------------------------"
        print " |Table\t|Event \t|Date \t\t|Age \t|Blurb"
        print " |----------------------------------------------------------------------------------------------"
        print " |Dem \t|1 \t|%s \t|0.00 \t|Birth Date" % self.demographics['Date_of_Birth']
        for event in events:
            if len(event['Blurb']) > 50:
                blurb = "%s..." % event['Blurb'][:50]
            else:
                blurb = event['Blurb']
            print " |%s \t|%s \t|%s \t|%s \t|%s" % (event['Table'], str(event['EventId']), event['Date'], str(event['Age']), blurb )
        if self.demographics['Date_of_Death']:
            print " |Dem \t|1 \t|%s \t|    \t|Birth Date" % self.demographics['Date_of_Birth']
        print " |______________________________________________________________________________________________\n"



    #--------------------------------------------------------------------------------------------
    def event( self, tableName, eventId ):

        # validate args
        if tableName:
            tableDefinition = [ t for t in self.datasetTableDefinitions if t.name in tableName ][0]
        else:
            print "Warning! '%s' is not a valid RPDR table." % tableName
            return
        if not eventId:
            print "Warning! Must provide RPDR event ID."
            return

        # search for event
        qResult = None
        with self.dbCon:
            dbCur = self.dbCon.cursor()
            dbCur.execute( "SELECT * FROM %s WHERE EMPI = ? AND rowid = ? LIMIT 1" % tableDefinition.name, (self.empi,eventId) )
            qResult = dbCur.fetchone()
            if qResult is None:
                print "Warning! Query for event returned nothing."
                return
        eventCols = [c for c in qResult]

        # determine spacing after name
        colLength = 0
        for col in tableDefinition.columns:
            if len(col.name) > colLength:
                colLength = len(col.name)
        
        print " _______________________________________________________________________________________________\n |"

        # print table name
        spacing = ''.join([ ' ' for i in xrange(colLength - len("Table")) ])
        print " |Table:%s %s" % (spacing, tableDefinition.name)

        # account for last column containing a free-text report
        spacing = "|%s" % ''.join([ ' ' for i in xrange(colLength+1) ])
        eventCols[len(eventCols)-1] = eventCols[len(eventCols)-1].replace('\n', '\n %s ' % spacing)

        # print columns
        for cIdx, col in enumerate(tableDefinition.columns):
            spacing = ''.join([ ' ' for i in xrange(colLength - len(col.name)) ])
            print " |%s:%s %s" % (col.name, spacing, eventCols[cIdx])

        print " |______________________________________________________________________________________________\n"



    #--------------------------------------------------------------------------------------------
    def writeNote( self, author, note ):

        self.patientNotes.write( author, self.empi, note )



    #--------------------------------------------------------------------------------------------
    def deleteNotes( self, noteIds ):
        
        self.patientNotes.delete( noteIds )



    #--------------------------------------------------------------------------------------------
    def printNotes( self ):
        
        self.patientNotes.printAll( self.empi )




class PatientNotes:
    
    #--------------------------------------------------------------------------------------------
    def __init__( self, dataset, tableName='PatientNotes' ):
        
        # RPDR dataset
        self.dataset = dataset

        # database info
        self.dbPath = self.dataset.dbPath
        self.dbCon = self.dataset.dbCon

        # name of database table containing patient notes
        self.patientNotesTableName = 'PatientNotes'

        # check if the patient notes database table exists
        qResult = None
        with self.dbCon:
            dbCur = self.dbCon.cursor()

            dbCur.execute( "SELECT table_name FROM information_schema.tables WHERE table_type=\'BASE TABLE\' AND table_schema=\'rpdr\' AND table_name='%s'" % self.patientNotesTableName.lower() )

            qResult = dbCur.fetchone()

        if qResult is None:
            # patient notes table doesn't exist - create table in database
            qCreate = "CREATE TABLE " + self.patientNotesTableName + " ( id INTEGER PRIMARY KEY, Author TEXT NOT NULL, CreatedTimestamp TIMESTAMP DEFAULT CURRENT_TIMESTAMP NOT NULL, Empi TEXT NOT NULL, Note TEXT NOT NULL )"
            with self.dbCon:
                dbCur = self.dbCon.cursor()
                dbCur.execute(qCreate)
                print "Created database table '%s'." % self.patientNotesTableName



    #--------------------------------------------------------------------------------------------
    def write(self, author, empi, note):
        
        # check that args are valid strings
        if not author or not isinstance(author, str):
            print "Error! Must provide an author string."
            return
        if not empi or not isinstance(empi, str):
            print "Error! Must provide an empi string."
            return
        if not note or not isinstance(note, str):
            print "Error! Must provide a note string."
            return
            
        with self.dbCon:
            dbCur = self.dbCon.cursor()

            # check that the patient exists
            dbCur.execute( "SELECT count(*) FROM Mrn WHERE Enterprise_Master_Patient_Index = ?", (empi,) )
            if dbCur.fetchone()[0] == 0:
                print "Warning! The patient with EMPI %d was not found in the Mrn table." % empi
                return

            # record note
            dbCur.execute( "INSERT INTO %s ( Author, Empi, Note ) VALUES ( ?, ?, ? )" % self.patientNotesTableName, ( author, empi, note ) )



    #--------------------------------------------------------------------------------------------
    def delete(self, noteIds):
        
        # check that at least 1 note ID was provided as a list
        if not isinstance( noteIds, list ):
            print "Warning! Nothing deleted. Must provide a list of note IDs."
            return
        
        numIds = len( noteIds )
        if numIds == 0:
            print "Warning! Nothing deleted. Must provide a list of note IDs."
            return
        
        # loop through list of note ids
        for noteId in noteIds:
            
            with self.dbCon:
                dbCur = self.dbCon.cursor()

                # check note's existence
                dbCur.execute( "SELECT count(*) FROM %s WHERE id = ?" % self.patientNotesTableName, (noteId,) )
                if dbCur.fetchone()[0] == 0:
                    print "Warning! Nothing deleted. The patient note with id %d was not found!" % noteId
                    return

                # delete note
                dbCur.execute( "DELETE FROM %s WHERE id = ?" % self.patientNotesTableName, (noteId,) )



    #--------------------------------------------------------------------------------------------
    def printAll(self, empi):

        with self.dbCon:
            dbCur = self.dbCon.cursor()

            # check that the patient exists
            dbCur.execute( "SELECT count(*) FROM Mrn WHERE Enterprise_Master_Patient_Index = ?", (empi,) )
            if dbCur.fetchone()[0] == 0:
                print "Warning! The patient with EMPI %d was not found in the Mrn table." % empi
                return

            # get patient notes
            dbCur.execute( "SELECT * FROM %s WHERE Empi = ?" % self.patientNotesTableName, (empi,) )
            qResult = dbCur.fetchall()
            if qResult is None  or len(qResult) == 0:
                print "This patient has no notes."
                return
            notes = qResult

            # print notes
            print " _______________________________________________________________________________________________\n |"
            print " | Patient Notes ( EMPI = %s )" % empi
            print " |----------------------------------------------------------------------------------------------"
            print " |id \t|Timestamp \t\t|Author \t|Note"
            print " |----------------------------------------------------------------------------------------------"
            for note in notes:
                if len(note['Note']) > 50:
                    blurb = "%s..." % note['Note'][:50]
                else:
                    blurb = note['Note']
                print " |%s \t|%s \t|%s \t|%s" % (note['id'], str(note['CreatedTimestamp']), note['Author'], blurb )
            print " |______________________________________________________________________________________________\n"











