import os
import time
from concurrent.futures import ThreadPoolExecutor, as_completed

import requests


def download_video_part(url, start, end, output):
    headers = {'Range': f'bytes={start}-{end}'}
    response = requests.get(url, headers=headers)

    with open(output, 'wb+') as f:
        for chunk in response.iter_content(1024):
            f.write(chunk)


if __name__ == '__main__':
    url = "https://sample-videos.com/video123/mp4/720/big_buck_bunny_720p_5mb.mp4"  # 5MB
    chunk_size = 1000000  # 1MB
    output = "test.mp4"

    # get header with file length only
    get_start = time.time()
    response = requests.head(url)
    file_size = int(response.headers['Content-Length'])
    print("file_size: %.2fMB" % (file_size / chunk_size))

    # parallel download
    chunks = range(0, file_size, chunk_size)
    with ThreadPoolExecutor(max_workers=10) as executor:
        for i, start in enumerate(chunks):
            executor.submit(download_video_part, url, start,
                            start + chunk_size - 1, f'{output}.part{i}')
        executor.shutdown(wait=True)
    print("%.2fs" % (time.time() - get_start))

    # merge chunks
    with open(output, 'wb+') as o:
        for i in range(len(chunks)):
            with open(f'{output}.part{i}', 'rb') as s:
                o.write(s.read())
            os.remove(chunk_path)
