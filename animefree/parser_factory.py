import re
from parser import Anime1Parser, FileParser
from urllib.parse import urlparse


class ParserFactory():
    def get_parser(self, url: str):
        # first try supported hosts
        host = urlparse(url).netloc
        if host == Anime1Parser.host:
            return Anime1Parser()

        # finally try file parser by parsing file extention
        file_ext_match = re.match(r'.*\.(\w+$)', url)
        if file_ext_match and file_ext_match.group(1) in FileParser.support_extensions:
            return FileParser()

        # nothing we can do...
        raise Exception("url not support: %s" % url)
