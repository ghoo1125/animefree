import abc
import re
from concurrent.futures import ThreadPoolExecutor, as_completed
from typing import List

import requests
from bs4 import BeautifulSoup


class Parser(abc.ABC):
    def __init__(self, thread_num):
        self.executor = ThreadPoolExecutor(max_workers=thread_num)
        self.title = ""
        self.ext = ""

    @abc.abstractmethod
    def parse(self, url) -> List[str]:
        return NotImplemented

    def fetch_urls(self, mapper, urls) -> List[str]:
        futures = []
        for url in urls:
            futures.append(self.executor.submit(mapper, url))

        # as_completed is unordered, loop through manually
        results = []
        for future in futures:
            results.extend(f.result() for f in as_completed([future]))

        return results

    def get_and_parse(self, url) -> BeautifulSoup:
        response = requests.get(url)
        return BeautifulSoup(response.text, 'lxml')


class FileParser(Parser):
    support_extensions = {"mp4", "jpg"}

    def __init__(self):
        self.thread_num = 1
        super().__init__(self.thread_num)

    # override
    def parse(self, url) -> List[str]:
        file_tile_ext_match = re.match(r'.*\/(\w+)\.(\w+$)', url)
        if file_tile_ext_match is None:
            raise Exception("could not parse %s" % url)

        self.title = file_tile_ext_match.group(1)
        self.ext = file_tile_ext_match.group(2)

        return [url]


class Anime1Parser(Parser):
    host = "anime1.cc"

    def __init__(self):
        self.thread_num = 10
        super().__init__(self.thread_num)

    # override
    def parse(self, url) -> List[str]:
        soup = self.get_and_parse(url)
        self.title = soup.title.text.split("-")[0].strip()
        # TODO dynamically fetch file extension
        self.ext = ".mp4"
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
