# code for i/o handling in the freezam project
# Graham Arthur (garthur), Carnegie Mellon University

import io
import os
import sys
import logging
import urllib

import numpy as np
import pydub
from scipy.io import wavfile as wav

# setup logging
logger = logging.getLogger('fz.io')

# directory constants
ROOT_DIR = os.path.abspath(os.path.join(os.path.dirname(__file__), '..'))
TEMP_DIR = os.path.join(ROOT_DIR, "temp")

class locationtype:
    FILE = 0
    URL = 1
    SOCKET = 2

# READER FUNCTIONS

def file_reader(location):
    """
    reads a function from a file at location
    """
    # change to absolute path if necessary
    if (not os.path.exists(location)): 
        location = os.path.abspath(location)

    extension = location.rsplit(".", 1)[-1].lower()
    logger.info("data is in file at " + location)
    # only reads wav files
    if (extension != "wav"):
        logger.error("cannot read files of type " + extension + "!")
        raise Exception("cannot read files of type " + extension)
    
    rate, data = wav.read(location)
    return rate, data

def url_reader(location):
    """
    reads a function from a url at location
    """
    logger.info("data is in url at " + location)
    # get the filename
    temp_file = location.rsplit('/', 1)[-1]
    temp_file = os.path.join(TEMP_DIR, "data", temp_file)
    # open location with urllib and write to temp/data
    urllib.request.urlretrieve(location, temp_file)
    logger.info("file retrieved to " + temp_file)
    # return the file_reader result
    return file_reader(temp_file)

def socket_reader(location):
    """
    reads a function from a socket at location
    """
    # TODO: implement this
    pass

def get_reader(ltype):
    """
    takes in a location type (ltype) and gets the appropriate file reader,
    one of file_reader, url_reader, and socket_reader and then returns it
    """
    readers = [file_reader, url_reader, socket_reader]
    return readers[ltype]

def get_ltype(location):
    """
    takes in a location string and returns one of locationtype
    (file, url, or socket)
    """
    # check for a file location
    if (os.path.exists(os.path.abspath(location))):
        ltype = locationtype.FILE
    # check if it is a valid URL
    elif (urllib.parse.urlparse(location).scheme in ["http", "https"]):
        ltype = locationtype.URL
    # TODO: check if it is a valid socket
    elif (False):
        ltype = locationtype.SOCKET
    else:
        logger.error(location + " is not a valid file, url or socket. cannot read.")
        raise Exception(location + " is not a valid file, url or socket. cannot read.")
    return ltype

def read_song(location):
    """ 
    takes in a file location (location) gets the appropriate file 
    reader using get_reader, and then returns the result of that 
    reader on location
    """
    try:
        # get the appropriate reader and load the data
        logger.info("reading data...")
        reader = get_reader(get_ltype(location))
        rate, audio = reader(location)
        # turn into one-channel data
        audio = np.mean(audio, axis=1)
        logger.info("read!")
        return rate, audio
    except:
        logger.error("fatal error in read_song ", exc_info = True)
        sys.exit()