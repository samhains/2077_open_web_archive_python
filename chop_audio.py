from pydub import AudioSegment
import os

INPUT_DIR = './cosmic_radio'
OUTPUT_DIR = './cosmic_radio_chopped'


def get_filenames(dir_name):
    return [INPUT_DIR +"/"+fname
            for fname in os.listdir(dir_name)
            if fname.endswith('.m4a')]


i = 0
song_num = 1

input_filenames = get_filenames(INPUT_DIR)

for fname in input_filenames:
    full_audio = AudioSegment.from_file(fname, "m4a")
    t = 0
    song_num = song_num + 1
    while  t < len(full_audio):
        i = i + 1
        interval_length = 2000
        t1 = t
        t2 =  t + interval_length
        audio_sample = full_audio[t1:t2]
        audio_sample.export(OUTPUT_DIR +'/cosmic_radio{}_{}.mp3'.format(song_num, i), format="mp3") #Exports to a wav file in the current path
        t = t2
