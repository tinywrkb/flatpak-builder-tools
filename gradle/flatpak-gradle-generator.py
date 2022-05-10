#!/usr/bin/env python3

__license__ = 'MIT'
import aiohttp
import argparse
import asyncio
import json
import hashlib
import logging
import re

async def get_remote_sha256(url):
    logging.info(f"started sha256({url})")
    sha256 = hashlib.sha256()
    async with aiohttp.ClientSession(raise_for_status=True) as http_session:
        async with http_session.get(url) as response:
            while True:
                data = await response.content.read(4096)
                if not data:
                    break
                sha256.update(data)
    logging.info(f"done sha256({url})")
    return sha256.hexdigest()

async def parse_url(url):
    ret = [{ 'type': 'file',
            'url': url,
            'sha256': await get_remote_sha256(url),
            'dest': 'dependencies/flatRepo', }]
    return ret

async def parse_urls(urls):
    sources = []
    sha_coros = []
    for url in urls:
        sha_coros.append(parse_url(str(url)))
    sources.extend(sum(await asyncio.gather(*sha_coros), []))
    return sources

def main():
    parser = argparse.ArgumentParser()
    parser.add_argument('input', help='The gradle log file')
    parser.add_argument('output', help='The output JSON sources file')
    args = parser.parse_args()

    urls = []
    r = re.compile('(?:(?:https?|ftp):\/\/)?[\w/\-?=%.]+\.[\w/\-?=%.]+')
    with open(args.input,'r') as f:
        for lines in f:
            res = r.findall(lines)
            if len(res) > 0:
                for url in res:
                    if url.endswith('.jar'):
                        urls.append(url)

    # print(urls)

    sources = asyncio.run(parse_urls(urls))

    with open(args.output, 'w') as fp:
        json.dump(sources, fp, indent=4)
        fp.write('\n')


if __name__ == '__main__':
    main()
