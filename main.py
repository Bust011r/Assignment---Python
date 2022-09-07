import os
import sys
import aiohttp
import asyncio
import aiofiles
import time
import signal


def check_connection_timeout(start_time):
    connection_timeout = 30  # seconds
    if time.time() > start_time + connection_timeout:
        raise Exception(
            f'Unable to download other images after {connection_timeout} seconds of ConnectionErrors')
    else:
        time.sleep(1)


def signal_handler(signum, frame):
    while True:
        selection = str(
            input('are you sure you want stop the script? ')).capitalize()
        if selection == 'Y':
            exit()
        elif selection == 'N':
            break
        else:
            print('correct value are only "Y" or "N"')


async def read_file(file):
    try:
        async with aiofiles.open(file, mode='r') as f:
            contents = await f.read()
            await f.close()
        lines = contents.splitlines()
    except:
        print(f'{file} not finded')
        exit()

    return lines


async def write_file(resp, dest_path):
    dl = 0
    total_length = int(resp.headers.get('content-length'))
    async with aiofiles.open(dest_path, mode='wb') as f:
        async for data in resp.content.iter_chunked(1024):
            dl += len(data)
            await f.write(data)
            done = int(50 * dl / total_length)
            sys.stdout.write("\r[%s%s]" % ('=' * done, ' ' * (50-done)))
            sys.stdout.flush()
        await f.close()


async def request(session, url, path):
    async with session.get(url) as resp:
        if resp.ok:
            file_name = url.rsplit('/', 1)[1]
            dest_path = os.path.join(path, file_name)
            # write only if not exist yet the image
            if not os.path.exists(dest_path):
                await write_file(resp, dest_path)
                print(f'download of {file_name} completed')
            else:
                print(f'{file_name} yet in directory selected')
        else:
            print(f'error code {resp.status}')
            if resp.status == 404:
                # do something??
                pass


async def download_images(urls, path):
    async with aiohttp.ClientSession() as session:
        for url in urls:
            start_time = time.time()
            # try while connection_timeout
            while True:
                try:
                    await request(session, url, path)
                    break
                # handle if the connection itself has got in trouble
                except aiohttp.ClientConnectorError as e:
                    check_connection_timeout(start_time)


async def main():
    if len(sys.argv) == 2:
        path = sys.argv[1]
        if os.path.exists(path):
            urls = await read_file('input.txt')
            await download_images(urls, path)
        else:
            print('The directory didn\'t exist')
    elif len(sys.argv) < 2:
        print('Add a directory to save the images')
    else:
        print('More than 1 parameter can\'t be accepted')


signal.signal(signal.SIGINT, signal_handler)
asyncio.run(main())
