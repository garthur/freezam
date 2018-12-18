DROP TABLE IF EXISTS fz_parameters;
DROP TABLE IF EXISTS fz_song_signatures;
DROP TABLE IF EXISTS fz_song_data;
DROP TABLE IF EXISTS fz_song_library;

CREATE TABLE fz_parameters (
    window_fn TEXT,
    window_size INTEGER,
    window_shift INTEGER,
    kernel TEXT,
    octaves INTEGER,
    hash_fn INTEGER,
    num_matches INTEGER,
    threshold_epsilon NUMERIC
);

CREATE TABLE fz_song_library (
    song_id TEXT PRIMARY KEY,
    title TEXT,
    artist TEXT,
    album TEXT,
    release_date TEXT,
    samp_rate INTEGER,
    length NUMERIC
);

CREATE TABLE fz_song_signatures (
    id SERIAL PRIMARY KEY,
    song_id TEXT,
    sig_type TEXT,
    sig_ REAL[][],
    FOREIGN KEY (song_id) REFERENCES fz_song_library (song_id) ON DELETE CASCADE
);

CREATE TABLE fz_song_data (
    id SERIAL PRIMARY KEY,
    song_id TEXT,
    data BYTEA,
    FOREIGN KEY (song_id) REFERENCES fz_song_library (song_id) ON DELETE CASCADE
);