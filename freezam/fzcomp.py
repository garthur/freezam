# code for handling computations in the freezam project
# Graham Arthur (garthur), Carnegie Mellon University

import logging
import warnings
from copy import copy

import math
import numpy as np
import matplotlib.pyplot as plt
from scipy import signal
from scipy import spatial
from skimage import util

warnings.filterwarnings("ignore")
logger = logging.getLogger('fz.comp')

# PERIODOGRAMS

def compute_periodogram(series, samp_rate, h=10, delta=1, window_fn="hamming"):
    """
    given some signal (series), sampling rate, window size (in seconds), 
    window shift (in seconds) and window function, compute the periodogram
    """
    H = h * samp_rate
    SHIFT = delta * samp_rate
    
    # slice time series into windows of length (h*samp_rate), stepping by
    # delta*samp_rate
    slices = util.view_as_windows(series, window_shape=(H,), step=SHIFT)
    logger.info("windows computed!")
    # throw away series for memory
    del series
    
    # compute the local periodograms
    freq = signal.periodogram(slices[0], fs=samp_rate, window=window_fn)[0]
    logger.info("frequencies computed!")
    pdgrams = [signal.periodogram(win_slice, fs=samp_rate, window=window_fn)[1]
                    for win_slice in slices]
    
    logger.info("local periodograms computed!")
    return np.array(pdgrams)

def smooth_periodogram(l_pdgram, kernel):
    # TODO implement this
    """
    given set of local periodograms (l_pdgrams), 
    smooth them using some kernel choice (kernel)
    """
    pass

def plot_periodogram(freq, pdgram):
    """
    given a periodogram (pdgram) and a set of frequencies, plot the periodogram
    """
    plt.figure()
    plt.semilogy(freq, pdgram)
    plt.ylim([1e-7, 1e2])
    plt.xlabel('Frequency [Hz]')
    plt.ylabel('PSD [V**2/Hz]')
    plt.show()

def plot_spectrogram(series, samp_rate, window_fn="hamming", 
                     h=10, title="", save_location=None):
    # TODO: TEST this from an entry_point
    """
    takes a set of local periodograms (l_pdgrams), constructs 
    a spectrogram, and then plots it
    """
    plt.figure()
    # compute the spectrogram
    f, t, Sxx = signal.spectrogram(series, samp_rate, 
                                   window=window_fn, 
                                   nperseg=h)
    # create a mesh color plot of the spectrogram
    plt.pcolormesh(t, f, Sxx)
    plt.title(title)
    plt.xlabel("Time [s]")
    plt.ylabel("Frequency [Hz]")
    if save_location is None:
        plt.show()
    else:
        plt.savefig(save_location)
        

# SIGNATURES
def compute_sig_posfreq(l_pdgrams, samp_rate):
    """
    computes a signature from local periodograms (l_pdgram) using
    the peak positive frequency method
    """
    logger.info("computing the positive frequency signature...")
    signatures = []
    # loop through the periodograms
    for pdgram in l_pdgrams:
        # find the index where the maximum power occurs
        f = np.argmax(pdgram)/(samp_rate/2)
        # record that frequency normalized to [0, 1]
        signatures.append([f])
    
    return np.array(signatures)

def compute_sig_maxpow(l_pdgrams, samp_rate, m=8):
    """
    computes a signature from local pdgrams (l_pdgram) using
    the maximum power method
    """
    logger.info("computing the max power signature...")
    min_freq = (2**-(m+1))*(samp_rate/2)
    signatures = []
    
    # loop through the periodograms
    for pdgram in l_pdgrams:
        start = 0
        l_sig = []
        
        # compute the signature for the kth octave
        for k in range(0, m):
            width = math.ceil((2**k) * min_freq)
            l_sig.append(max(pdgram[start:start+width]))
            start += width
        signatures.append(copy(l_sig))
    
    logger.info("max power signature computed!")
    return np.array(signatures)

def compute_sig(l_pdgrams, samp_rate, sig_type="maxpow"):
    """
    computes the appropriate signature from the local periodograms
    """
    sig_dict = {"maxpow":compute_sig_maxpow, "posfreq":compute_sig_posfreq}
    return sig_dict[sig_type](l_pdgrams, samp_rate)

# HASHES
def compute_hash_wang(sig, h_table):
    """
    computes a hashed wang signature from the local periodograms
    """
    pass

# SEARCH
def match_signature(sig_snippet, sig_full, epsilon=1000, dist=spatial.distance.euclidean):
    """
    compares two signatures and determines if they match
    """
    # get the snippet lengths
    len_snippet = len(sig_snippet)
    len_full = len(sig_full)

    # if the signatures are equal in length, just do a pairwise comparison on the two
    if (len_full == len_snippet):
        pairs = zip(sig_snippet, sig_full)
        dists = [dist(x, y) for x, y in pairs]
        return all([(d < epsilon) for d in dists])

    # otherwise, search for the start of the signature
    for i in range(0, len_full - len_snippet):
        pairs = zip(sig_snippet, sig_full[i:i + len_snippet])
        dists = [dist(x, y) for x, y in pairs]
        if all([d < epsilon for d in dists]):
            return True
    return False