import sys
import aiohttp
from tqdm import tqdm

async def download_ts(url, filename, save_path):
    """异步下载.ts文件，带有进度条"""
    async with aiohttp.ClientSession() as session:
        async with session.get(url) as response:
            total_size = int(response.headers.get('content-length', 0))
            with open(save_path / filename, 'wb') as f, tqdm(total=total_size, unit='B', unit_scale=True, desc=filename) as pbar:
                async for chunk in response.content.iter_chunked(1024):
                    f.write(chunk)
                    pbar.update(len(chunk))

if __name__ == "__main__":
    import asyncio
    from pathlib import Path
    
    url = sys.argv[1]
    filename = sys.argv[2]
    save_path = Path(sys.argv[3])
    
    asyncio.run(download_ts(url, filename, save_path))
