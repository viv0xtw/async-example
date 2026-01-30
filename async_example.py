from aiohttp import ClientSession, ClientTimeout
from dotenv import load_dotenv
from pathlib import Path
from time import perf_counter

import asyncio
import os
import aiofiles


# Post Review Scope Analysis
load_dotenv()

NASA_IMAGE_URL = os.environ.get('NASA_APOD_API_BASE_URL')
NASA_API_KEY = os.environ.get('NASA_APOD_API_KEY')

if not NASA_API_KEY or not NASA_IMAGE_URL:
    raise ValueError("Environment variables not found.")

if not os.path.exists('images'):
    Path.mkdir(Path(__file__).parent / 'images', exist_ok=True, parents=True)

max_concurrency = 200
semaphore = asyncio.Semaphore(max_concurrency)
CLIENT_TIMEOUT = 30

async def image_api_call(url: str, session: ClientSession, timeout: ClientTimeout = ClientTimeout(CLIENT_TIMEOUT),
                         params: dict | None = None):
    async with semaphore:
        async with session.get(url, timeout=timeout, params=params) as response:
            print(response.url)
            if not response.ok:
                response.raise_for_status()
            return await response.content.read()


async def save_image(response_content: bytes, filename: str):
    async with aiofiles.open(os.path.join(str(Path(__file__).parent / 'images'), filename), 'wb') as f:
        await f.write(response_content)


async def rest_api_call(url: str, session: ClientSession, timeout: ClientTimeout = ClientTimeout(CLIENT_TIMEOUT),
                        params: dict | None = None):
    async with session.get(url, timeout=timeout, params=params) as response:
        # print(response.url)
        if not response.ok:
            response.raise_for_status()
        return await response.json()
    return None


async def process_image(url, session, filename):
    content = await image_api_call(url, session)
    await save_image(content, filename)
    print(f"{filename} saved!")


async def async_main(count: int = 5):
    s = perf_counter()
    query_parameters = {
        'count': count,
        'start_date': '2025-03-01',
        'end_date': '2025-09-30',
        "api_key": NASA_API_KEY
    }
    async with ClientSession() as session:
        base_info = await rest_api_call(NASA_IMAGE_URL, session, params=query_parameters)
        t1 = perf_counter()
        print(f'Fetched Image Details in :{t1-s:.2f}')
        filtered_media = [d for d in base_info if d.get('media_type') == 'image']

        image_media = [{
            'title': i.get('title'),
            'url': i.get('url'),
            'date': i.get('date'),
            'filename': i.get('url', '/').split('?')[0].split('/')[-1]
        } for i in filtered_media]

        tasks = []
        for image in image_media:
            tasks.append(process_image(image.get('url'), session=session, filename=image.get('filename')))
            # tasks.append(image_api_call(image.get('url'), session=session))
        results = await asyncio.gather(*tasks, return_exceptions=True)
        t2 = perf_counter()

        failed = 0
        for image, result in zip(image_media, results):
            if isinstance(result, Exception):
                # print(f'Failed for: {image.get("url")} {result}')
                failed += 1

        print(f'Downloaded {len(image_media) - failed}/{len(image_media)} images in :{t2 - t1:.2f}. Failed tasks: {failed}')