# code for handling songs, including searching for a song
# Graham Arthur (garthur), Carnegie Mellon University

import logging
import uuid

import fzcomp
import fzdb
import fzio

logger = logging.getLogger("fz.song")

# SONG OBJECT

class SongEntry(object):
    """
    representations of objects
    """

    def __init__(self, address, title="", artist="", album="", date="", 
                 window_fn="hamming"):
        """
        initializes a songEntry from a song object returned by the
        io package, including populating all the fields above
        """
        # required argument
        self.address = address
        # optional arguments to init
        self.title = title
        self.artist = artist
        self.album = album
        self.date = date
        
        # computed on initialization
        self.song_id = str(uuid.uuid4())
        logger.info("all metadata added for song " + self.song_id)
        # read data
        logger.info("creating SongEntry from address at " + address)
        self.samp_rate, data = fzio.read_song(address)
        self.length = round(len(data) / self.samp_rate, 2)
        
        # perform spectral analysis
        self.l_pdgrams = fzcomp.compute_periodogram(
            data,
            self.samp_rate,
            window_fn = window_fn
        )
        logger.info("spectral analysis complete!")