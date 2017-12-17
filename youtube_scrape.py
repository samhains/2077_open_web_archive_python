from bs4 import BeautifulSoup
import requests

import subprocess
import youtube_dl
import os
from utility import *


class MyLogger(object):
    def debug(self, msg):
        pass

    def warning(self, msg):
        pass

    def error(self, msg):
        print(msg)


def my_hook(d):
    if d['status'] == 'finished':
        print('Done downloading, now converting ...')


ydl_opts = {
    'format': '18',
    'logger': MyLogger(),
    'progress_hooks': [my_hook],
}

def youtube_scrape(search_term):
    search_term = search_query_from_str(search_term)
    make_folder(search_term)

    url = "https://www.youtube.com/results?search_query={}&page=1".format(search_term)
    r = requests.get(url)
    data = r.text

    soup = BeautifulSoup(data, "html.parser")
    video_links = []

    for link in soup.find_all("a"):
        link_name = link.get('href')
        if link_name.startswith("/watch?v="):
            full_link = "http://youtube.com"+link_name
            if full_link not in video_links:
                video_links.append(full_link)

    i = 1
    for video_link in video_links:
        command = "youtube-dl -o {}/{}.mp4 -f 134 --max-filesize 10m {}".format(search_term, i, video_link)
        print(command)
        try:
            print(subprocess.check_output(command.split(" ")))
            i = i +1
        except:
            print("ERR")
