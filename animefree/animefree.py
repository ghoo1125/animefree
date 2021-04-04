import abc
import math
import os
import time
from concurrent.futures import ThreadPoolExecutor, as_completed
from typing import List
from urllib.parse import urlparse

import requests
from bs4 import BeautifulSoup


class Parser(abc.ABC):
    def __init__(self):
        self.executor = ThreadPoolExecutor(max_workers=10)
        self.title = ""

    @abc.abstractmethod
    def parse(self, url) -> List[str]:
        return NotImplemented

    def fetch_urls(self, mapper, urls) -> List[str]:
        futures = []
        for url in urls:
            futures.append(self.executor.submit(mapper, url))
        return [future.result() for future in as_completed(futures)]

    def get_and_parse(self, url) -> BeautifulSoup:
        response = requests.get(url)
        return BeautifulSoup(response.text, 'lxml')


class Anime1Parser(Parser):
    host = "anime1.cc"

    def __init__(self):
        super().__init__()

    # override
    def parse(self, url) -> List[str]:
        soup = self.get_and_parse(url)
        self.title = soup.title.text.split("-")[0].strip()
        anchors = self.__find_episode_anchors(soup)
        video_links = self.fetch_urls(self.__find_video_link, anchors)
        return self.fetch_urls(self.__find_target_url, video_links)

    def __find_episode_anchors(self, soup) -> List[str]:
        episode_anchors = soup.select('ul.eps > li > a.e-aa.mr-2')
        episode_ids = [a["href"] for a in episode_anchors]
        return ["https://" + Anime1Parser.host + id for id in episode_ids]

    def __find_video_link(self, url) -> str:
        soup = self.get_and_parse(url)
        return "https://" + Anime1Parser.host + soup.find(id="play").find("iframe")["src"]

    def __find_target_url(self, url) -> str:
        soup = self.get_and_parse(url)
        return soup.find(id="default_video").find("source")["src"]


def download_video_part(url, start, end, output):
    headers = {'Range': f'bytes={start}-{end}'}
    response = requests.get(url, headers=headers)

    with open(output, 'wb+') as f:
        for chunk in response.iter_content(1024):
            f.write(chunk)
    return response.status_code


def download_video(url, output):
    # get header with file length only
    response = requests.head(url)
    file_size = int(response.headers['Content-Length'])
    thread_num = 20
    chunk_size = math.ceil(file_size / thread_num)
    print("file_size: %.2fMB" % (file_size / 1000000))

    # parallel download chunks
    chunks = range(0, file_size, chunk_size)
    futures = []
    with ThreadPoolExecutor(max_workers=thread_num) as executor:
        for i, start in enumerate(chunks):
            futures.append(executor.submit(download_video_part, url,
                           start, start + chunk_size - 1, f'{output}.part{i+1}'))
        print([future.result()
              for future in as_completed(futures, timeout=600)])

    # merge chunks
    with open(output, 'wb+') as o:
        for i in range(len(chunks)):
            with open(f'{output}.part{i+1}', 'rb') as s:
                o.write(s.read())
            os.remove(f'{output}.part{i+1}')


if __name__ == '__main__':
    # TODO parse args
    url = "https://anime1.cc/208507504/"

    # validate hosts
    support_hosts = {Anime1Parser.host}
    host = urlparse(url).netloc
    if host not in support_hosts:
        raise Exception("host not support: %s" % url)

    # parse and get target urls
    target_urls = []
    parser = None
    if host == Anime1Parser.host:
        parser = Anime1Parser()
        target_urls = parser.parse(url)
    outputs = [
        f"{parser.title}-{i}.mp4" for i in range(len(target_urls), 0, -1)]
    target_urls = target_urls[0:1]
    outputs = outputs[0:1]
    print("target_urls:", target_urls)
    print("outputs:", outputs)

    # start parallel download videos
    start = time.time()
    # with ThreadPoolExecutor(max_workers=len(target_urls)) as executor:
    #     for url, output in zip(target_urls, outputs):
    #         executor.submit(download_video, url, output)
    #     executor.shutdown(wait=True)
    for url, output in zip(target_urls, outputs):
        download_video(url, output)
    print("%.2fs time spent" % (time.time() - start))
