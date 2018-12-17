# code for database read/write actions for the freezam project
# Graham Arthur (garthur)

import os
import sys
import logging
import shutil
import pickle
import tabulate
import psycopg2
import numpy as np

import fzcomp

logger = logging.getLogger('fz.db')

# TODO: test this
class FileSystemDB(object):
    """
    provides functions for reading and writing to a database
    represented as a file system
    """

    def __init__(self, db_settings, param_settings):
        """
        initializes a file system databaser 
        """
        logger.info("initializing file databaser...")
        db_root = db_settings["address"]
        self.fz_song_lib = os.path.join(db_root, "fz_song_lib")
        self.fz_song_sigs = os.path.join(db_root, "fz_song_sigs")
        self.fz_song_data = os.path.join(db_root, "fz_song_data")
        # if these paths don't exist, make them
        try:
            if (not os.path.exists(self.fz_song_lib)):
                logger.warn(self.fz_song_lib + " does not exist, creating...")
                os.makedirs(self.fz_song_lib)
                logger.info("home directory created")
            if (not os.path.exists(self.fz_song_sigs)):
                logger.warn(self.fz_song_sigs + " does not exist, creating...")
                os.makedirs(self.fz_song_sigs)
                logger.info("home directory created")
            if (not os.path.exists(self.fz_song_data)):
                logger.warn(self.fz_song_data + " does not exist, creating...")
                os.makedirs(self.fz_song_data)
                logger.info("home directory created")
            self.params = param_settings
            logger.info("file databaser initialized!")
        except:
            logger.error("error in file database setup", exc_info=True)
            sys.exit()

    def write(self, song_entry):
        """
        writes a song_entry to the database, including moving files if necessary
        """
        s = song_entry
        lib_file = os.path.join(self.fz_song_lib, song_entry.song_id + ".pkl")
        sig_file = os.path.join(self.fz_song_sigs, song_entry.song_id + ".pkl")
        song_file = os.path.join(self.fz_song_data, song_entry.song_id + ".wav")
        # use pickle to dump the song entry object into the various files
        try:
            logger.info("writing " + s.song_id + " to the library...")
            # write in the metadata
            with open(lib_file, 'wb') as output:
                lib_info = [s.song_id, s.title, s.artist, s.album, s.date]
                pickle.dump(lib_info, output, pickle.HIGHEST_PROTOCOL)
            # write in the signatures
            with open(sig_file, "wb") as output:
                sigs = {"maxpow":fzcomp.compute_sig_maxpow(s.l_pdgrams, s.samp_rate), 
                        "posfreq":fzcomp.compute_sig_posfreq(s.l_pdgrams, s.samp_rate)}
                pickle.dump(sigs, output, pickle.HIGHEST_PROTOCOL)
            # write in the files
            # if the file is in temp, we move it to the db
            if ("temp" in s.address):
                shutil.move(s.address, song_file)
            # otherwise, copy it from its initial location
            else:
                shutil.copyfile(s.address, song_file)
            logger.info("song " + s.song_id + " has been written to the database!")
        except:
            logger.error("failed to write song " + s.song_id + " to the database",
                         exc_info = True)

    def remove(self, song_id):
        try:
            os.remove(os.path.join(self.fz_song_lib, song_id + ".pkl"))
            os.remove(os.path.join(self.fz_song_sigs, song_id + ".pkl"))
            os.remove(os.path.join(self.fz_song_data, song_id + ".wav"))
        except:
            logger.error("failed to remove song " + song_id + " from the database", 
                         exc_info = True)

    def lookup(self, song_info):
        """
        looks up a song given some metadata song_info, returns song_id. not to be 
        confused with search, which matches signatures
        """
        pass

    def get_info(self, song_id):
        """
        load a SongEntry object into memory from its id
        """
        data = os.path.join(self.fz_song_lib, song_id + ".pkl")
        try:
            with open(data, "rb") as song_file:
                song = pickle.load(song_file)
            return song
        except:
            logger.error("song " + song_id + " not found in database")
        

    def update_record(self, song_id, new_info):
        """
        updates a certain song_id with new_info
        """
        pass

    def iterate(self):
        """
        creates a generator for the database that can be iterated through
        """
        for song in os.listdir(self.fz_song_lib):
            song_id = song.rsplit(".", 1)[0]
            yield self.get_info(song_id)
        
    def list_db(self):
        """
        list the entire database
        """
        headers = ["id", "title", "artist", "album", "date"]
        rows = []
        for song in self.iterate():
            rows.append(song)
        return rows

    def update_db(self, new_func):
        """
        traverse the entire database and update the data 
        (perhaps with a new window function) et. cetera
        """
        pass

    def slow_search(self, snippet, num_matches=1):
        """
        linearly searches the database for a snippet of the data 
        """
        matches = []
        
        sig_snippet = fzcomp.compute_sig(snippet.l_pdgrams, snippet.samp_rate,
                                         self.params["search"]["sig_type"])

        logger.info("slow searching through the database...")
        for song in os.listdir(self.fz_song_sigs):
            # get the appropriate signature from the file
            sig_full = pickle.load(os.path.join(self.fz_song_sigs, song + ".pkl"))[self.params["search"]["sig_type"]]
            # if a song matches, then add it's info to our list of matches
            if (fzcomp.match_signature(sig_snippet, sig_full)):
                matches.append(self.get_info(song))
                logger.info("result " + str(len(matches)) + " found!")
            # if we have enough matches, stop looking
            if (len(matches) == num_matches):
                break
        return None if len(matches) == 0 else matches

    def clear(self):
        """
        clears the entire database, for testing purposes
        """
        logger.info("clearing library...")
        try:
            for data in os.listdir(self.fz_song_lib):
                song_id = data.rsplit(".", 1)[0]
                self.remove(song_id)
        except:
            logger.error("clearing the library failed", exc_info=True)
        logger.info("library empty!")

class PostgreSQLDB:
    """
    provides functions for reading and writing to a database
    represented as a posgreSQL db
    """
    def __init__(self, db_settings, param_settings):
        """
        initializes a postgresql databaser
        """
        self.host = db_settings["address"]
        self.db = db_settings["db"]
        self.user = db_settings["username"]
        self.pw = db_settings["password"]
        # store parameters
        self.params = param_settings

        conn = None
        logger.info("initializing postgresql databaser...")
        try:
            conn = psycopg2.connect(host=self.host, database=self.db, 
                                    user=self.user, password=self.pw)
            cur = conn.cursor()
            cur.execute("""
                        SELECT window_fn, window_size, window_shift, kernel
                        FROM fz_parameters
                        """)
            params = cur.fetchone()

            if (False):
                logger.warn("specified settings do not match, defaulting to database parameters")
            cur.close()
            logger.info("postgresql databaser initialized!")
        except:
            logger.error("database setup failed, aborting...", exc_info=True)
            sys.exit()
        finally:
            if conn is not None:
                conn.close()

    @staticmethod
    def __list_to_arr(l):
        arr = str(l.tolist())
        arr = arr.replace("[", "{")
        arr = arr.replace("]", "}")
        arr = arr.replace("\n", ",")
        return arr

    def write(self, song_entry):
        """
        writes a song_entry to the database, including moving files if necessary
        """
        conn = None
    
        logger.info("writing song " + song_entry.song_id + " into the library")
        # sql commands
        insert_dat = """
                     INSERT INTO fz_song_library (
                        title, artist, album, release_date,
                        samp_rate, length
                     ) VALUES (%s, %s, %s, %s, %s, %s)
                     RETURNING song_id;
                     """
        insert_sig = """
                     INSERT INTO fz_song_signatures(song_id, sig_type, sig_)
                     VALUES (%s, %s, %s);
                     """
        try:
            # connect to db
            conn = psycopg2.connect(host=self.host, database=self.db, 
                                    user=self.user, password=self.pw)
            cur = conn.cursor()
            # insert data
            s = song_entry
            logger.info("inserting song metadata")
            cur.execute(insert_dat, (s.title, s.artist, s.album, s.date, 
                                     s.samp_rate, s.length))
            song_id = cur.fetchone()[0]
            logger.info("inserting song signatures")
            # cur.execute(insert_sig, (song_id, "pdgram", PostgreSQLDB.__list_to_arr(s.l_pdgrams)))
            cur.execute(insert_sig, 
                        (song_id, "maxpow", 
                         PostgreSQLDB.__list_to_arr(fzcomp.compute_sig_maxpow(s.l_pdgrams, s.samp_rate))))
            cur.execute(insert_sig,
                        (song_id, "posfreq",
                        PostgreSQLDB.__list_to_arr(fzcomp.compute_sig_posfreq(s.l_pdgrams, s.samp_rate))))
            # commit and clean up
            conn.commit()
            cur.close()
            logger.info("song " + song_entry.song_id + " has been written to the library!")
        except:
            logger.error("there was a problem writing " + song_entry.song_id + " to the libary", exc_info=True)
        finally:
            if conn is not None:
                conn.close()
        
    def remove(self, song_id):
        """
        removes a song with a given song_id from the library
        """
        conn = None

        delete_sql = """
                     DELETE FROM fz_song_library WHERE song_id = %s;
                     """
        try:
            # connect to db
            conn = psycopg2.connect(host=self.host, database=self.db, 
                                    user=self.user, password=self.pw)
            cur = conn.cursor()
            # run delete commands
            cur.execute(delete_sql, song_id)
            conn.commit()
            cur.close()
            logger.info("song " + song_id + " has been removed from the library!")
        except:
            logger.error("there was a problem removing " + song_id + " from the library")
        finally:
            if conn is not None:
                conn.close()

    def lookup(self, song_info):
        # TODO: set this up, probably need some preprocessing on song entry
        """
        looks up a song given some metadata song_info, returns song_id. not to be 
        confused with search, which matches signatures
        """
        pass

    def update_record(self, song_id, new_info):
        # TODO: set this up
        """
        updates a certain song_id with new_info
        """
        pass

    def list_db(self):
        """
        list the entire database
        """
        logger.info("listing the database")
        headers = ["id", "title", "artist", "album", "date", "length"]
        rows = []
        conn = None
        list_sql = """
                   SELECT song_id, title, artist, album, release_date, length
                   FROM fz_song_library;
                   """
        try:
            # connect to db
            conn = psycopg2.connect(host=self.host, database=self.db, 
                                    user=self.user, password=self.pw)
            cur = conn.cursor()
            # run the list command
            cur.execute(list_sql)
            rows = cur.fetchall()
            # clean up
            cur.close()
        except:
            logger.error("there was an error in listing the database")
        finally:
            if conn is not None:
                conn.close()

        return rows

    def slow_search(self, snippet, num_matches=1):
        """
        linearly searches the database for a snippet of the data 
        """
        conn = None
        matches = []
        results = []
        sig_sql = """
                  SELECT song_id, sig_ 
                  FROM fz_song_signatures WHERE sig_type = %s;
                  """
        inf_sql = """
                  SELECT song_id, title, artist, album, release_date, length
                  FROM fz_song_library WHERE song_id = %s;
                  """
        sig_snippet = fzcomp.compute_sig(snippet.l_pdgrams, snippet.samp_rate,
                                         self.params["search"]["sig_type"])
        try:
            logger.info("slow searching through the database...")
            conn = psycopg2.connect(host=self.host, database=self.db, 
                                    user=self.user, password=self.pw)
            cur = conn.cursor()
            cur.execute(sig_sql, (self.params["search"]["sig_type"],))
            song = cur.fetchone()

            while song is not None:
                # do the actual comparison
                # pull the signature from the song
                sig_full = np.array(song[1])
                # and match it
                if (fzcomp.match_signature(sig_snippet, sig_full, 
                                            epsilon=self.params["search"]["threshold_epsilon"])):
                    matches.append(song[0])
                    logger.info("result " + str(len(matches)) +" found!")
                # if we have reached num_matches, break
                if (len(matches) == num_matches):
                    logger.info("DONE!")
                    break
                # otherwise get the next row
                song = cur.fetchone()
            # if there are no matches, return None
            if matches == []:
                return None
            # otherwise, get the song information
            for match in matches:
                cur.execute(inf_sql, (match,))
                results.append(cur.fetchall()[0])
            return results
        except:
            logger.error("could not search for the provided snippet", exc_info = True)
        finally:
            if conn is not None:
                conn.close()

    def search(self, snippet, num_matches=1):
        # TODO: build this
        """
        searches the database using locality sensitive hashing
        """
        pass

    def clear(self):
        """
        clears the entire database, for testing purposes
        """
        conn = None

        delete_sql = """
                     DELETE FROM fz_song_library;
                     """
        try:
            logger.info("clearing the database...")
            conn = psycopg2.connect(host=self.host, database=self.db, 
                                    user=self.user, password=self.pw)
            cur = conn.cursor()
            cur.execute(delete_sql)
            conn.commit()
            cur.close()
            logger.info("database cleared!")
        except:
            logger.error("could not clear database")
        finally:
            if conn is not None:
                conn.close()


