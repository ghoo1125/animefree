import sys
import time

from downloader import Downloader
from parser_factory import ParserFactory

if __name__ == '__main__':
    # examples
    # url = "https://1251316161.vod2.myqcloud.com/5f6ddb64vodsh1251316161/965a74b45285890815026939627/y3wMFAQUF3cA.mp4"
    # url = "https://file-examples-com.github.io/uploads/2017/04/file_example_MP4_1280_10MG.mp4"
    # url = "https://anime1.cc/208507504/"

    # parse target url
    args = sys.argv
    if (len(args) != 2):
        raise Exception("usage: python3 animefree.py {url}")
    target_url = args[1]

    # parse and get target file urls
    parser = ParserFactory().get_parser(target_url)
    target_file_urls = parser.parse(target_url)
    outputs = [
        f"{parser.title}-{i}.{parser.ext}" for i in range(len(target_file_urls), 0, -1)]
    target_file_urls = target_file_urls[0:2]
    outputs = outputs[0:2]
    print("target_files:", target_file_urls)
    print("outputs:", outputs)

    # there is network bandwidth bottleneck so we simply downloads the files sequentially
    start = time.time()
    downloader = Downloader()
    for url, output in zip(target_file_urls, outputs):
        print(downloader.download_video(url, output))
    print("%.2fs time spent" % (time.time() - start))
