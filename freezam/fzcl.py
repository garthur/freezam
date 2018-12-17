# command line implementation and main function for the freezam project
# Graham Arthur (garthur), Carnegie Mellon University

import os
import sys
import json
import argparse
import logging

import fzsong
import fzdb

class Freezam(object):

    def __init__(self):
        # initial locations
        self.root = os.path.abspath(os.path.join(os.path.dirname(__file__), '..'))
        self.log_file = os.path.join(self.root, "temp" + os.sep + "freezam.log")
        
        # get settings
        self.db_settings = os.path.join(self.root,"settings" + os.sep + "db.json")
        with open(self.db_settings) as d:
            self.db_settings = json.load(d)
        self.parameters = os.path.join(self.root, "settings" + os.sep + "param.json")
        with open(self.parameters) as p:
            self.parameters = json.load(p)

        # set up argument parsing
        parser = argparse.ArgumentParser(
            description="command line interface for running a free version of shazam",
            usage="freezam [OPTIONS] subcommand [OPTIONS] [ARGUMENTS]")
        parser.add_argument("-v", "--verbose", action="store_true", 
            help="activates verbose logging"
        )
        subparsers = parser.add_subparsers()

        # parser for add subcommand
        parser_add = subparsers.add_parser("add")
        parser_add.set_defaults(subcommand = self.add)
        parser_add.add_argument("song", type=str, 
            help="location from which to add a song to the library"
        )
        parser_add.add_argument("--title", type=str, help="song title", default="")
        parser_add.add_argument("--artist", type=str, help="artist name", default="")
        parser_add.add_argument("--album", type=str, help="album name", default="")
        parser_add.add_argument("--date", type=str, help="release date", default="")
        
        # parser for ingest subcommand
        parser_ingest = subparsers.add_parser("ingest")
        parser_ingest.set_defaults(subcommand = self.ingest)
        parser_ingest.add_argument("dir", type=str,
            help="directory from which to add songs to the library"
        )
        
        # parser for remove subcommand
        parser_remove = subparsers.add_parser("remove")
        parser_remove.set_defaults(subcommand = self.remove)
        parser_remove.add_argument("id", type=str, help="song id")
        
        # parser for identify subcommand
        parser_identify = subparsers.add_parser("identify")
        parser_identify.set_defaults(subcommand = self.identify)
        parser_identify.add_argument("snippet", type=str, 
            help="location for a snippet to be identified"
        )
        parser_identify.add_argument("--slow", action="store_true", default=False,
            help="performs a slow linear search, for testing purposes"
        )
        parser_identify.add_argument("--matches", type=int, default=1)
        
        # parser for lib subcommand
        parser_lib = subparsers.add_parser("lib")
        parser_lib.set_defaults(subcommand = self.lib)

        # parser for clear subcommand
        parser_clear = subparsers.add_parser("clear")
        parser_clear.set_defaults(subcommand = self.clear)

        # parse arguments
        args = parser.parse_args(sys.argv[1:])

        # set up logger
        # if the old logging file exists, remove it, then make a new one
        if os.path.exists(self.log_file):
            os.remove(self.log_file)
        f = open(self.log_file, "w+")
        f.close()
        # configure the logger
        logging.basicConfig(filename=self.log_file, level=logging.DEBUG)
        self.logger = logging.getLogger("fz")
        # create console handler and send everything if verbose
        ch = logging.StreamHandler(sys.stdout)
        if args.verbose:
            ch.setLevel(logging.DEBUG)
        else:
            ch.setLevel(logging.ERROR)
        # create formatter and add to the handlers
        fm = logging.Formatter("%(asctime)s - %(name)s - %(levelname)s - %(message)s")
        ch.setFormatter(fm)
        # add handlers to the logger
        self.logger.addHandler(ch)

        self.logger.info("settings read!")
        self.logger.info("argument parsing set up!")
        self.logger.info("logger set up!")

        # set up databaser
        if (self.db_settings["db_type"] == "sql"):
            self.databaser = fzdb.PostgreSQLDB(self.db_settings["sql"], self.parameters)
        elif (self.db_settings["db_type"] == "file"):
            self.databaser = fzdb.FileSystemDB(self.db_settings)
        else:
            self.logger.error("invalid database type specified")
            exit(1)

        # log an unrecognized subcommand and exit
        if not callable(args.subcommand):
            self.logger.error('unrecognized subcommand')
            parser.print_help()
            exit(1)
            
        # go to subcommand
        args.subcommand(args)

    def add(self, args):
        """
        top-level handler for adding a song to the persistent database
        """
        # now actually add to the library
        song = fzsong.SongEntry(args.song, title=args.title, artist=args.artist,
                                album=args.album, date=args.date)
        self.databaser.write(song)

    def ingest(self, args):
        """
        top-level handler for ingesting a directory of songs
        """
        self.logger.info("ingesting...")
        for dirpath, _, filenames in os.walk(args.dir):
            for f in filenames:
                self.logger.info(f)
                song_path = os.path.abspath(os.path.join(dirpath, f))
                song = fzsong.SongEntry(song_path, title=f, album=args.dir)

                self.databaser.write(song)

    def remove(self, args):
        """
        top-level handler for removing a song from the existing library
        """
        self.logger.info("removing song " + args.id + " from library")
        self.databaser.remove(args.id)

    def clear(self, args):
        """
        top-level handler for clearing the database, for testing purposes
        """
        self.databaser.clear()

    def identify(self, args):
        """
        top-level handler for identifying a song from an existing song library
        """
        self.logger.info("identifying the provided snippet...")
        snippet = fzsong.SongEntry(args.snippet)
        result = self.databaser.slow_search(snippet, num_matches=args.matches)
        self.logger.info("done!")
        print(result)

    def lib(self, args):
        """
        top-level handler for listing songs from the current song library
        """
        self.logger.info("listing library...")
        print(self.databaser.list_db())

if __name__ == "__main__":
    Freezam()