import sys
import aiohttp
from tqdm import tqdm

async def download_ts(url, filepath):
    """异步下载.ts文件，带有进度条"""
    async with aiohttp.ClientSession() as session:
        async with session.get(url) as response:
            total_size = int(response.headers.get('content-length', 0))
            with open(filepath, 'wb') as f, tqdm(total=total_size, unit='B', unit_scale=True, desc=filepath.split('\\')[-1]) as pbar:
                async for chunk in response.content.iter_chunked(1024):
                    f.write(chunk)
                    pbar.update(len(chunk))

if __name__ == "__main__":
    import asyncio
    from pathlib import Path
    
    url = sys.argv[1]
    filepath = sys.argv[2]
    
    asyncio.run(download_ts(url, filepath))
