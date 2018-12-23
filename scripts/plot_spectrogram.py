from context import freezam
from freezam import fzcomp
from freezam import fzio

# read in the test file
test_file = "../temp/data/her_focus.wav"
samp_rate, data = fzio.read_song(test_file)
# spectral analysis
freq, l_pdgrams = fzcomp.compute_periodogram(data, samp_rate)

fzcomp.plot_spectrogram(data, samp_rate)