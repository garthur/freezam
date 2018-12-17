# code for testing non-library functions in freezam
# Graham Arthur (garthur), Carnegie Mellon University

import os
import unittest
import random
import math
import numpy as np

from .context import freezam
from freezam import fzsong
from freezam import fzcomp
from freezam import fzio

class TestHelpers(object):

    @staticmethod
    def sample_audio(samp_rate=40000, length=30):
        """
        sample audio from a test signal (sine wave) with gaussian noise
        for (length) seconds sampled at (samp_rate) Hz
        """
        amp = 2 * np.sqrt(2)
        freq = 1234
        noise_power = 0.001 * samp_rate / 2
        time = np.arange(0, length, 1/samp_rate)
        audio = amp*np.sin(2*np.pi*freq*time)
        audio += np.random.normal(scale=np.sqrt(noise_power), size=time.shape)
        return audio

    @staticmethod
    def get_test_song():
        test_song = os.path.join(os.path.dirname(os.path.abspath(__file__)), "test", "wn_full.wav")
        return fzsong.SongEntry(test_song, title="FULL", artist="TEST")

    @staticmethod
    def get_test_snippet():
        # grab a random snippet from the test folder
        test_snippet = os.path.join(os.path.dirname(os.path.abspath(__file__)), "test", "wn_snip{0}.wav".format(random.randint(1,4)))
        return fzsong.SongEntry(test_snippet, title="SNIPPET", artist="TEST")
    
    @staticmethod
    def get_test_filesystem_databaser():
        return fzdb.FileSystemDB(None)

class TestFreezamComp(unittest.TestCase):

    def test_pdgram(self):
        # sample audio from a test signal (sine wave) with noise sampled
        # at 44kHz
        samp_rate = 40000
        audio = TestHelpers.sample_audio(samp_rate)
        
        window_size = 10
        window_shift = 1
        
        pdgrams = fzcomp.compute_periodogram(audio, samp_rate, h=window_size, delta=window_shift)

        # pdgram entries should be > 0
        for pdgram in pdgrams:
            for density in pdgram:
                self.assertGreaterEqual(density, 0)

    def test_pdgram_dim(self):
        # sample audio
        samp_rate = 40000
        audio = TestHelpers.sample_audio(samp_rate)
        
        window_size = 10
        window_shift = 1
        
        pdgrams = fzcomp.compute_periodogram(audio, samp_rate, h=window_size, delta=window_shift)
        
        num_windows = len(range(0, len(audio) - (window_size * samp_rate) + 1, (window_shift * samp_rate)))
        # there should be num_windows pdgrams
        self.assertEqual(len(pdgrams), num_windows)
    
    def test_wrong_windows(self):
        # sample white noise
        samp_rate = 40000
        audio = TestHelpers.sample_audio(samp_rate)
        
        with self.assertRaises(Exception):
            # test wide window
            fzcomp.compute_periodogram(audio, samp_rate, h=50, delta=1)
            # test no shift
            fzcomp.compute_periodogram(audio, samp_rate, h=10, delta=0)
            # test wide shift
            fzcomp.compute_periodogram(audio, samp_rate, h=10, delta=11)

    def test_sig(self):
        samp_rate = 40000
        audio = TestHelpers.sample_audio(samp_rate)
        pdgrams = fzcomp.compute_periodogram(audio, samp_rate, h=10, delta=1)

    def test_sig_dim(self):
        # sample audio
        samp_rate = 40000
        audio = TestHelpers.sample_audio(samp_rate)
        pdgrams = fzcomp.compute_periodogram(audio, samp_rate, h=10, delta=1)

        for k in range(0, 10):
            M = random.randint(0, 11)
            sigs = fzcomp.compute_sig_maxpow(pdgrams, samp_rate, m=M)
            # each signature should have M octaves
            self.assertEqual(len(sigs[0]), M)
            # there should be a signature for every periodogram
            self.assertEqual(len(sigs), len(pdgrams))

    def test_sig_match(self):
        # sample audio
        samp_rate = 40000
        audio = TestHelpers.sample_audio(samp_rate)

        pdgrams = fzcomp.compute_periodogram(audio, samp_rate, h=10, delta=1)
        sigs = fzcomp.compute_sig_maxpow(pdgrams, samp_rate)

        # subset the signatures to get snippets
        snip_min_len = 100
        for k in range(0, 10):
            rand_start = random.randint(0, len(audio) - snip_min_len)
            rand_end = random.randint(rand_start + snip_min_len, len(audio))

            snip_sig = sigs[rand_start:rand_end]

            # snippet should match the full signatures
            self.assertTrue(fzcomp.match_signature(snip_sig, sigs))
            # and itself
            self.assertTrue(fzcomp.match_signature(snip_sig, snip_sig))

class TestFreezamIO(unittest.TestCase):

    def test_get_reader(self):
        self.assertEqual(fzio.get_reader(fzio.locationtype.FILE), fzio.file_reader)
        self.assertEqual(fzio.get_reader(fzio.locationtype.SOCKET), fzio.socket_reader)
        self.assertEqual(fzio.get_reader(fzio.locationtype.URL), fzio.url_reader)
        with self.assertRaises(IndexError):
            fzio.get_reader(79)

class TestFreezamDB(unittest.TestCase):

    def test_filesystem_db(self):
        
        test_song = TestHelpers.get_test_song()
        test_snippet = TestHelpers.get_test_snippet()
        databaser = TestHelpers.get_test_filesystem_databaser()

        # test adding
        databaser.write(test_song)
        found = False
        for song in databaser.iterate():
            found = (test_song.song_id == song.song_id)
            if found: break
        self.assertTrue(found)

        # test remove
        databaser.remove(test_song.song_id)
        found = False
        for song in databaser.iterate():
            found = (test_song.song_id == song.song_id)
        self.assertFalse(found)

        # test slow search
        self.assertIsNone(databaser.slow_search(test_snippet))

        databaser.write(test_song)
        self.assertIsNotNone(databaser.slow_search(test_snippet))
        databaser.remove(test_song.song_id)

if __name__ == "__main__":
    unittest.main()