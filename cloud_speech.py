# [START import_libraries]
from __future__ import division

import re
import sys
import os
import wave

import gif_scrape
from google.cloud import speech
import random
import threading
from utility import *
import time

from pythonosc import udp_client
from pythonosc import dispatcher
from pythonosc import osc_server
from concurrent.futures import ThreadPoolExecutor

from google.cloud.speech import enums
from google.cloud.speech import types
import pyaudio
from six.moves import queue
# [END import_libraries]
phone_picked_up = True
# Audio recording parameters
RATE = 16000
CHUNK = int(RATE / 10)  # 100ms
client = udp_client.SimpleUDPClient("localhost", 7401)

streaming = True
last_folder  = "start"

client.send_message("/cloud_speek", " :start")
time.sleep(1)

delete_old("gifs_1")
delete_old("gifs_2")

is_search = False

p = pyaudio.PyAudio()
for i in range(p.get_device_count()):
    print(p.get_device_info_by_index(i))

def turn_off_streaming():
    global streaming
    streaming = False
    client.send_message("/scene", "i_am_lost.mp3")

def client_message_sender(response, scene,  keywords):
    if response in keywords:
        print('sending client message', scene)
        send_client_message(scene)


def send_client_message(scene):
        client.send_message("/scene", scene+".mp3")


class AudioFile:
    chunk = 1024

    def __init__(self, file):
        """ Init audio stream """
        self.wf = wave.open(file, 'rb')
        self.p = pyaudio.PyAudio()
        self.stream = self.p.open(
            format = self.p.get_format_from_width(self.wf.getsampwidth()),
            channels = self.wf.getnchannels(),
            rate = self.wf.getframerate(),
            output = True
        )

    def play(self):
        """ Play entire file """
        data = self.wf.readframes(self.chunk)
        while data != b'':
            self.stream.write(data)
            data = self.wf.readframes(self.chunk)

    def close(self):
        """ Graceful shutdown """
        self.stream.close()
        self.p.terminate()

class MicrophoneStream(object):
    """Opens a recording stream as a generator yielding the audio chunks."""
    def __init__(self, rate, chunk):
        self._rate = rate
        self._chunk = chunk

        # Create a thread-safe buffer of audio data
        self._buff = queue.Queue()
        self.closed = True

    def __enter__(self):
        self._audio_interface = pyaudio.PyAudio()
        self._audio_stream = self._audio_interface.open(
            format=pyaudio.paInt16,
            # The API currently only supports 1-channel (mono) audio
            # https://goo.gl/z757pE
            input_device_index=1,
            channels=1, rate=self._rate,
            input=True, frames_per_buffer=self._chunk,
            # Run the audio stream asynchronously to fill the buffer object.
            # This is necessary so that the input device's buffer doesn't
            # overflow while the calling thread makes network requests, etc.
            stream_callback=self._fill_buffer,
        )

        self.closed = False

        return self

    def __exit__(self, type, value, traceback):
        self._audio_stream.stop_stream()
        self._audio_stream.close()
        self.closed = True
        # Signal the generator to terminate so that the client's
        # streaming_recognize method will not block the process termination.
        self._buff.put(None)
        self._audio_interface.terminate()

    def _fill_buffer(self, in_data, frame_count, time_info, status_flags):
        """Continuously collect data from the audio stream, into the buffer."""
        self._buff.put(in_data)
        return None, pyaudio.paContinue

    def generator(self, start_time):
        global phone_picked_up
        while not self.closed and phone_picked_up:
            # elapsed_time = time.time() - start_time
            # if elapsed_time
            # Use a blocking get() to ensure there's at least one chunk of
            # data, and stop iteration if the chunk is None, indicating the
            # end of the audio stream.
            chunk = self._buff.get()
            if chunk is None:
                return
            data = [chunk]

            # Now consume whatever other data's still buffered.
            while True:
                try:
                    chunk = self._buff.get(block=False)
                    if chunk is None:
                        return
                    data.append(chunk)
                except queue.Empty:
                    break

            yield b''.join(data)
# [END audio_stream]


def get_filenames(dir_name):
    return [fname
            for fname in os.listdir(dir_name)
            if fname.endswith('.mp3')]

def play_audio(fname):
    print("playing", fname)
    a = AudioFile(fname)
    a.play()
    a.close()

def listen_print_loop(responses):
    global is_search
    """Iterates through server responses and prints them.

    The responses passed is a generator that will block until a response
    is provided by the server.

    Each response may contain multiple results, and each result may contain
    multiple alternatives; for details, see https://goo.gl/tjCPAU.  Here we
    print only the transcription for the top alternative of the top result.

    In this case, responses are provided for interim results as well. If the
    response is an interim one, print a line feed at the end of it, to allow
    the next result to overwrite it, until the response is a final one. For the
    final one, print a newline to preserve the finalized transcription.
    """

    num_chars_printed = 0
    for response in responses:
        if not response.results:
            continue

        # The `results` list is consecutive. For streaming, we only care about
        # the first result being considered, since once it's `is_final`, it
        # moves on to considering the next utterance.
        result = response.results[0]
        if not result.alternatives:
            continue

        # Display the transcription of the top alternative.
        transcript = result.alternatives[0].transcript

        overwrite_chars = ' ' * (num_chars_printed - len(transcript))
        global last_folder

        if not result.is_final:
            sys.stdout.write(transcript + overwrite_chars + '\r')
            sys.stdout.flush()

            num_chars_printed = len(transcript)

        else:
            response = transcript + overwrite_chars
            response = response.strip().lower()

            if response in ["about", "more information", "information", "more"]:

                time.sleep(1.0)
                is_search = False
                client.send_message("/scene", 3)
                play_audio("about.wav")

            if response in ["history", "the history"]:

                time.sleep(1.0)
                is_search = False
                play_audio("history.wav")
                client.send_message("/scene", 3)

            elif response in ["search", "i want to search"]:
                time.sleep(1.0)
                client.send_message("/scene", 1)
                is_search = True

                play_audio("search.wav")

            elif is_search:
                time.sleep(1.0)
                with ThreadPoolExecutor(max_workers=1) as executor:
                    f = executor.submit(play_audio, "searching.wav")

                if last_folder == "gifs_1":
                    new_folder = "gifs_2"
                if last_folder == "gifs_2" or last_folder == "start":
                    new_folder = "gifs_1"

                print("deleting stuff in unused folder", new_folder)
                try:
                    gif_scrape.gif_scrape(response, new_folder)
                    print("scrape success to unused folder", new_folder)
                    last_folder = new_folder
                    client.send_message("/cloud_speek", "{}:{}".format(response,new_folder))
                    play_audio("search_complete.wav")
                except ValueError:
                    play_audio("error_search.wav")
                    print("not enough items")

                is_search = False

            if re.search(r'\b(exit|quit|void)\b', transcript, re.I):
                print('Exiting..')
                send_client_message("exit")
                break

            num_chars_printed = 0



def microphone_stream(client,  streaming_config):
    with MicrophoneStream(RATE, CHUNK) as stream:
        start_time = time.time()
        audio_generator = stream.generator(start_time)
        requests = (types.StreamingRecognizeRequest(audio_content=content)
                    for content in audio_generator)

        responses = client.streaming_recognize(streaming_config, requests)
        # Now, put the transcription responses to use.
        listen_print_loop(responses)


def main():
    # See http://g.co/cloud/speech/docs/languages
    # for a list of supported languages.
    global phone_picked_up
    time.sleep(1.5)

    language_code = 'en-US'  # a BCP-47 language tag
    play_audio("welcome.wav")
    # threading.Timer(1, turn_off_streaming).start()
    client = speech.SpeechClient()
    config = types.RecognitionConfig(
        encoding=enums.RecognitionConfig.AudioEncoding.LINEAR16,
        sample_rate_hertz=RATE,
        language_code=language_code)
    streaming_config = types.StreamingRecognitionConfig(
        config=config,
        interim_results=True)
    while phone_picked_up:
        try:
            microphone_stream(client, streaming_config)
        except Exception as e:
            print(e)

def phone_state_changed(root, value):
    global phone_picked_up
    phone_picked_up = value
    if phone_picked_up:
        thread = threading.Thread(target=main, daemon=True)
        thread.start()

dispatcher = dispatcher.Dispatcher()
dispatcher.map("/phone", phone_state_changed)
server = osc_server.ThreadingOSCUDPServer(
      ("localhost", 7406), dispatcher)
print("Serving on {}".format(server.server_address))

server.serve_forever()
