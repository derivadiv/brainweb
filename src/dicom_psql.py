import os
from os.path import join, abspath
import sys
import dicom # pydicom package used to read DICOM image files
import psycopg2 # used to connect to PostGreSQL database
import psql # functions to connect to PostGreSQL database

# from dicom._dicom_dict import DicomDictionary
# tags = [d[4] for d in DicomDictionary.values()]

# Columns to be imported into database are here- TODO add more
tag_types = [
    ('id','SERIAL'),
    ('FilePath','TEXT UNIQUE NOT NULL'),
    ('SeriesDescription','TEXT'),
    ('StudyDescription', 'TEXT'),
    ('Manufacturer', 'TEXT'), 
    ('ManufacturerModelName', 'TEXT'),
    ('InstitutionName', 'TEXT'),
    ('PatientSex', 'VARCHAR(10)'),
    ('PatientAge', 'VARCHAR(10)'),
    ('SliceThickness', 'TEXT'),
    ('SpacingBetweenSlices', 'TEXT'),
    ('MagneticFieldStrength', 'TEXT'),
    ('ProtocolName', 'TEXT')
]

# TODO: debug pyplot package on supercloud, then import it. Longer-term TODO: put home-installed python packages in group-accessible place

# Connect to database, setup of needed schema/table(s)
def dbstart(coltags=tag_types):
    return psql.dbstart("dicom", "imagemeta", coltags)

# End connection
def dbend(conn):
    return psql.dbend(conn)

# Load DICOM metadata in headertags, output as dictionary
def load_dcm_meta(dcmpath, headertags=[t[0] for t in tag_types], savefolder=os.getcwd()):
    ds = dicom.read_file(dcmpath)
    savedict = {}
    for tag in headertags:
        if tag in ds:
            # sanitization done here
            savedict[tag] ="".join(i for i in ( str(ds.data_element(tag).value) ) if ord(i)<128)
        elif tag == 'FilePath':
            savedict['FilePath'] = dcmpath
        elif tag == 'id':
            pass
        else:
            # print 'Error: could not find tag ' + tag + ' in DICOM image ' + dcmpath + '\n'
            savedict[tag] = None
    savedict['FilePath'] = dcmpath
    return savedict

def insert_meta(conn, savedict):
    return psql.insert_dict(conn, savedict, "imagemeta")

if __name__=='__main__':
    # first argument is always script name; treat second as dcmpath
    if len(sys.argv) == 2:
        dirname = sys.argv[1]
        dcmfiles = []
        for root, dirs, files in os.walk(dirname):
            dcmfiles.extend([abspath(join(root, name)) for name in files if name[-4:] == '.dcm'])
        
        ans = raw_input('Found '+str(len(dcmfiles))+' DICOM files in directory. Continue? (type Y for yes, otherwise the program will abort)')

        if ans.lower() == 'y':
            conn = dbstart()
            # may want to print progress once the rest works
            for dcm in dcmfiles:
                savedict = load_dcm_meta(dcm) #TODO get rid of savedict? and just insert tuple directly
                insert_meta(conn, savedict)
            dbend(conn)

    else:
        print "Incorrect arguments. Usage: 'python dicom_psql.py <path_to_DICOM_folders>'"
        print "Currently, this script reads a DICOM file (the first argument) and stores its header information in the PostGreSQL database."

