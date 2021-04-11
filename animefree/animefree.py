import sys
import time

from downloader import Downloader
from parser_factory import ParserFactory

if __name__ == '__main__':
    # parse target url
    args = sys.argv
    if (len(args) != 2):
        raise Exception("usage: python3 animefree.py {url}")
    target_url = args[1]

    # # parse and get target file urls
    parser = ParserFactory().get_parser(target_url)
    target_file_urls = parser.parse(target_url)
    outputs = [
        f"{parser.title}-{i}.{parser.ext}" for i in range(len(target_file_urls), 0, -1)]
    print("target_files:", target_file_urls)
    print("outputs:", outputs)

    # there is network bandwidth bottleneck so we simply downloads the files sequentially
    start = time.time()
    downloader = Downloader()
    for url, output in zip(target_file_urls, outputs):
        print(downloader.download_video(url, output))
    print("%.2fs time spent" % (time.time() - start))
