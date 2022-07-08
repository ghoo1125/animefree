import math
import os
from concurrent.futures import ThreadPoolExecutor

import requests
from tqdm import tqdm


class Downloader():
    def __init__(self):
        self.thread_num = 10
        self.progress_bar_chunk_size = 10000  # 10KB
        self.executor = ThreadPoolExecutor(max_workers=self.thread_num)

    def download_video(self, url, output):
        # get header with file length only
        response = requests.head(url)
        file_size = int(response.headers.get('Content-Length', 0))
        print(file_size)
        chunk_size = math.ceil(file_size / self.thread_num)
        print("file_size: %.2fMB" % (file_size / 1000000))

        # parallel download chunks
        chunks = range(0, file_size, chunk_size)
        futures = []
        for i, start in enumerate(chunks):
            futures.append(self.executor.submit(self.download_video_part, url, start,
                                                start + chunk_size - 1, f'{output}.part{i+1}'))
        results = [future.result() for future in futures]

        # merge chunks
        with open(output, 'wb+') as o:
            for i in range(len(chunks)):
                with open(f'{output}.part{i+1}', 'rb') as s:
                    o.write(s.read())
                os.remove(f'{output}.part{i+1}')

        return results

    def download_video_part(self, url, start, end, output):
        headers = {'Range': f'bytes={start}-{end}'}
        response = requests.get(url, headers=headers, stream=True)
        total_size_in_bytes = int(response.headers.get('Content-Length', 0))
        progress_bar = tqdm(total=total_size_in_bytes,
                            unit='B', unit_scale=True)

        with open(output, 'wb+') as f:
            for chunk in response.iter_content(self.progress_bar_chunk_size):
                progress_bar.update(len(chunk))
                f.write(chunk)
        progress_bar.close()

        if total_size_in_bytes != 0 and progress_bar.n != total_size_in_bytes:
            print("ERROR, something went wrong")

        return response.status_code
