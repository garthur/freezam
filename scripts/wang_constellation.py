# exploring wang constellations for audio hashing

import matplotlib.pyplot as plt
import numpy as np

from context import freezam
from freezam import fzcomp
from freezam import fzio

# read in the test file
test_file = "../temp/data/her_focus.wav"
samp_rate, data = fzio.read_song(test_file)
# spectral analysis
freq, l_pdgrams = fzcomp.compute_periodogram(data, samp_rate)
# generate center, frequency pairs for the constellation
constellation = [np.arange(0, len(l_pdgrams)), [freq[np.argmax(pdgram)] for pdgram in l_pdgrams]]

# plot the constellation
plt.plot(constellation[0], constellation[1], "x")
plt.title("Wang Constellation")
plt.xlabel("Window Centers")
plt.ylabel("Frequency")
plt.show()
