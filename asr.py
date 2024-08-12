import os
import io
from faster_whisper import WhisperModel
import moviepy.editor as mp

def convert_ts_to_audio(ts_file_path):
    """将 .ts 文件转换为内存中的音频文件"""
    video = mp.VideoFileClip(ts_file_path)
    audio = video.audio

    # 将音频数据写入内存
    audio_buffer = io.BytesIO()
    audio.write_audiofile(audio_buffer, format='wav')
    audio_buffer.seek(0)  # 将文件指针移动到开始位置
    audio.close()
    video.close()
    
    return audio_buffer

def transcribe_audio(audio_buffer):
    """使用 faster-whisper 进行语音转文字"""
    model = WhisperModel("base")  # 选择合适的模型，例如 'base'、'small'、'medium'、'large'
    
    # 将内存中的音频数据转换为文件
    with io.BytesIO(audio_buffer.getvalue()) as temp_audio_file:
        result = model.transcribe(temp_audio_file)
    
    return result['segments']

def format_transcription_with_timestamps(segments):
    """将转录结果格式化为包含时间码的 .str 文件内容"""
    transcription = ""
    for segment in segments:
        start_time = segment['start']
        end_time = segment['end']
        text = segment['text']
        
        # 转换时间格式为 "HH:MM:SS"
        start_time_str = f"{int(start_time // 3600):02}:{int((start_time % 3600) // 60):02}:{int(start_time % 60):02}"
        end_time_str = f"{int(end_time // 3600):02}:{int((end_time % 3600) // 60):02}:{int(end_time % 60):02}"
        
        # 添加到转录文本
        transcription += f"{start_time_str} --> {end_time_str}\n{text}\n\n"
    
    return transcription

def process_folder(folder_path):
    """处理文件夹中的所有 .ts 文件"""
    for filename in os.listdir(folder_path):
        if filename.endswith(".ts"):
            ts_file_path = os.path.join(folder_path, filename)
            str_file_path = os.path.join(folder_path, filename.replace(".ts", ".str"))
            
            # 如果对应的 .str 文件存在，则跳过
            if os.path.exists(str_file_path):
                print(f"Skipping {filename}, .str file already exists.")
                continue
            
            # 将 .ts 文件转换为内存中的音频文件
            audio_buffer = convert_ts_to_audio(ts_file_path)
            
            # 使用 faster-whisper 进行语音转文字
            segments = transcribe_audio(audio_buffer)
            
            # 格式化转录结果为包含时间码的内容
            transcription = format_transcription_with_timestamps(segments)
            
            # 将转录结果保存到 .str 文件中
            with open(str_file_path, 'w', encoding='utf-8') as f:
                f.write(transcription)
            
            print(f"Processed {filename}, saved transcription to {str_file_path}")

if __name__ == "__main__":
    folder_path = "G:\网课"  # 替换为你的文件夹路径
    process_folder(folder_path)