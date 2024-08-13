import sys
import aiohttp
import asyncio
from tqdm import tqdm
from pathlib import Path

async def download_ts(url, filepath, retries=114):
    """异步下载.ts文件，带有进度条和重试机制"""
    attempt = 0
    while attempt < retries:
        try:
            # 定义临时文件路径
            tmp_filepath = f"{filepath}.tmp"
            
            async with aiohttp.ClientSession() as session:
                async with session.get(url) as response:
                    response.raise_for_status()  # 检查请求是否成功
                    total_size = int(response.headers.get('content-length', 0))
                    
                    # 创建文件夹（如果不存在）
                    Path(filepath).parent.mkdir(parents=True, exist_ok=True)
                    
                    with open(tmp_filepath, 'wb') as f, tqdm(total=total_size, unit='B', unit_scale=True, desc=Path(filepath).name) as pbar:
                        async for chunk in response.content.iter_chunked(1024):
                            f.write(chunk)
                            pbar.update(len(chunk))

                    # 验证下载文件大小是否与预期匹配
                    if total_size and Path(tmp_filepath).stat().st_size < total_size:
                        raise ValueError("下载文件不完整")

                    # 文件下载完成后，重命名临时文件为目标文件
                    Path(tmp_filepath).rename(filepath)
                    
                    print(f"下载完成: {filepath}")
                    break  # 下载成功，退出循环

        except (aiohttp.ClientError, ValueError, TimeoutError) as e:
            print(f"下载失败: {e}")
            attempt += 1
            if attempt >= retries:
                print(f"下载 {Path(filepath).name} 失败，已尝试 {retries} 次。")
                raise  # 重试次数用尽，重新抛出异常
            await asyncio.sleep(2)  # 等待 2 秒钟再重试

if __name__ == "__main__":
    url = sys.argv[1]
    filepath = sys.argv[2]
    asyncio.run(download_ts(url, filepath))
