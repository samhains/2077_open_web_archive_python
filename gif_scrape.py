import giphypop
import urllib
import numpy as np
from utility import *
import glob
import shutil
from multiprocessing.dummy import Pool as ThreadPool
pool = ThreadPool(100)

NUM_OF_GIFS = 8
def delete_old(folder_name):
    for the_file in os.listdir(folder_name):
        file_path = os.path.join(folder_name, the_file)
        try:
            if os.path.isfile(file_path):
                os.unlink(file_path)
            #elif os.path.isdir(file_path): shutil.rmtree(file_path)
        except Exception as e:
            print(e)

def geturl(url,folder_name, i):
    try:
        urllib.request.urlretrieve(url, "{}/{}.gif".format(folder_name, i))
    except:
        pass
def gif_scrape(search_term, folder_name):
    g = giphypop.Giphy()
    result_urls = [x.media_url for x in g.search(search_term)][:NUM_OF_GIFS]
    print("received  this number results:", len(result_urls))
    if len(result_urls) < 6:
        raise ValueError('Did not get enough results')

    results = pool.starmap(geturl, zip(result_urls, np.full(len(result_urls), folder_name), range(0, len(result_urls))))
    # for i, url in enumerate(result_urls):
    #     print('saving', url)
