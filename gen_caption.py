import whisper
import time
from zhconv import convert  # 简繁体转换
# from moviepy.editor import VideoFileClip


def seconds_to_hmsm(seconds):
    """
    输入一个秒数，输出为H:M:S:M时间格式
    @params:
        seconds   - Required  : 秒 (float)
    """
    hours = str(int(seconds // 3600))
    minutes = str(int((seconds % 3600) // 60))
    seconds = seconds % 60
    milliseconds = str(int(int((seconds - int(seconds)) * 1000)))  # 毫秒留三位
    seconds = str(int(seconds))
    # 补0
    if len(hours) < 2:
        hours = '0' + hours
    if len(minutes) < 2:
        minutes = '0' + minutes
    if len(seconds) < 2:
        seconds = '0' + seconds
    if len(milliseconds) < 3:
        milliseconds = '0'*(3-len(milliseconds)) + milliseconds
    return f"{hours}:{minutes}:{seconds},{milliseconds}"


def main():
    # 视频文件路径
    video_path = 'output/深度学习-video/深度学习-任雪梅-第4周 星期三 第4大节.mp4'
    # 输出音频文件路径
    # audio_output_path = 'output/audio.mp3'

    # # 加载视频文件
    # video = VideoFileClip(video_path)

    # # 30秒的音频
    # audio = video.audio.subclip(60, 2*60)

    # # 保存音频文件
    # audio.write_audiofile(audio_output_path)

    # # 释放资源
    # video.close()

    model = whisper.load_model("base", download_root="whisper_models/")

    start = time.time()
    result = model.transcribe(video_path, verbose=False, language="zh")
    print("Time cost: ", time.time() - start)

    for segment in result["segments"]:
        print(segment["start"], segment["end"], segment["text"])
    # 写入字幕文件
    with open(video_path.replace("mp4", "srt"), 'w', encoding='utf-8') as f:
        i = 1
        for r in result['segments']:
            f.write(str(i)+'\n')
            f.write(seconds_to_hmsm(float(r['start'])) +
                    ' --> '+seconds_to_hmsm(float(r['end']))+'\n')
            i += 1
            f.write(convert(r['text'], 'zh-cn')+'\n')  # 结果可能是繁体，转为简体zh-cn
            f.write('\n')


if __name__ == '__main__':
    main()
