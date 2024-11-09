import os
from pydub import AudioSegment
from io import BytesIO
from faster_whisper import WhisperModel

def convert_ts_to_audio(file_path):
    # 使用 pydub 提取音频
    audio = AudioSegment.from_file(file_path)
    
    # 将音频保存到 BytesIO 对象中
    audio_buffer = BytesIO()
    audio.export(audio_buffer, format="wav")
    audio_buffer.seek(0)
    
    return audio_buffer

def transcribe_audio(audio_buffer):
    """使用 faster-whisper 进行语音转文字"""
    model = WhisperModel("base", device='cuda')  # 选择合适的模型，例如 'base'、'small'、'medium'、'large'
    segments, _ = model.transcribe(audio_buffer, language="zh")  # 假设音频语言是中文，可以根据需要调整
    return list(segments)

def format_transcription_with_timestamps(segments):
    """将转录结果格式化为包含时间码的 .srt 文件内容"""
    transcription = ""
    for i, segment in segments:
        start_time = segment['start']
        end_time = segment['end']
        text = segment['text']
        
        # 转换时间格式为 "HH:MM:SS,SSS"
        start_time_str = f"{int(start_time // 3600):02}:{int((start_time % 3600) // 60):02}:{int(start_time % 60):02},{int((start_time % 1) * 1000):03}"
        end_time_str = f"{int(end_time // 3600):02}:{int((end_time % 3600) // 60):02}:{int(end_time % 60):02},{int((end_time % 1) * 1000):03}"
        
        # 添加到转录文本，SRT格式编号从1开始
        transcription += f"{i + 1}\n{start_time_str} --> {end_time_str}\n{text.strip()}\n\n"
    
    return transcription

def process_folder(folder_path):
    """处理文件夹中的所有 .ts 和 .mp4 文件"""
    for filename in os.listdir(folder_path):
        if filename.endswith(".ts") or filename.endswith(".mp4"):
            ts_file_path = os.path.join(folder_path, filename)
            srt_file_path = os.path.join(folder_path, filename.split('.')[0] + '.srt')
            
            # 如果对应的 .srt 文件存在，则跳过
            if os.path.exists(srt_file_path):
                print(f"Skipping {filename}, .srt file already exists.")
                continue
            
            # 将 .ts 文件转换为内存中的音频文件
            audio_buffer = convert_ts_to_audio(ts_file_path)
            
            # 使用 faster-whisper 进行语音转文字
            segments = transcribe_audio(audio_buffer)
            
            # 格式化转录结果为包含时间码的内容
            transcription = format_transcription_with_timestamps(segments)
            
            # 将转录结果保存到 .srt 文件中
            with open(srt_file_path, 'w', encoding='utf-8') as f:
                f.write(transcription)
            
            print(f"Processed {filename}, saved transcription to {srt_file_path}")

if __name__ == "__main__":
    folder_path = "G:\\网课"  # 替换为你的文件夹路径
    process_folder(folder_path)
