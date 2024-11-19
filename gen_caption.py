import whisper
import time
from zhconv import convert  # 简繁体转换
import sys
import os
import curses


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
        hours = "0" + hours
    if len(minutes) < 2:
        minutes = "0" + minutes
    if len(seconds) < 2:
        seconds = "0" + seconds
    if len(milliseconds) < 3:
        milliseconds = "0" * (3 - len(milliseconds)) + milliseconds
    return f"{hours}:{minutes}:{seconds},{milliseconds}"


def select_courses_interactive(videoList, title="选择视频文件:"):
    """使用光标交互式选择视频文件"""
    def draw_menu(stdscr, current_row, selected):
        stdscr.clear()
        h, w = stdscr.getmaxyx()
        
        stdscr.addstr(0, 0, title)
        stdscr.addstr(1, 0, "使用↑↓键移动, 回车选择/取消, y确认, q退出")
        stdscr.addstr(2, 0, "-" * (w-1))
        
        for idx, video in enumerate(videoList):
            y = idx + 4
            if y >= h:
                break
                
            mark = "[*]" if idx in selected else "[ ]"
            text = f"{mark} [{idx}]: {video}"
            
            if idx == current_row:
                stdscr.attron(curses.A_REVERSE)
                stdscr.addstr(y, 0, text[:w-1])
                stdscr.attroff(curses.A_REVERSE)
            else:
                stdscr.addstr(y, 0, text[:w-1])
        
        stdscr.refresh()

    def main(stdscr):
        curses.curs_set(0)
        current_row = 0
        selected = []
        
        while True:
            draw_menu(stdscr, current_row, selected)
            key = stdscr.getch()
            
            if key == curses.KEY_UP and current_row > 0:
                current_row -= 1
            elif key == curses.KEY_DOWN and current_row < len(videoList) - 1:
                current_row += 1
            elif key == ord('\n'):
                if current_row in selected:
                    selected.remove(current_row)
                else:
                    selected.append(current_row)
            elif key == ord('y'):
                if selected:
                    return selected
            elif key == ord('q'):
                return []
    
    return curses.wrapper(main)


def select_option_interactive(title, options, default_index=0):
    """通用的交互式单选菜单"""
    def draw_menu(stdscr, current_row):
        stdscr.clear()
        h, w = stdscr.getmaxyx()
        
        stdscr.addstr(0, 0, title)
        stdscr.addstr(1, 0, "使用↑↓键移动, 回车选择, q退出")
        stdscr.addstr(2, 0, "-" * (w-1))
        
        for idx, option in enumerate(options):
            y = idx + 4
            if y >= h:
                break
                
            if idx == current_row:
                stdscr.attron(curses.A_REVERSE)
                stdscr.addstr(y, 0, f"[{idx}] {option}")
                stdscr.attroff(curses.A_REVERSE)
            else:
                stdscr.addstr(y, 0, f"[{idx}] {option}")
        
        stdscr.refresh()

    def main(stdscr):
        curses.curs_set(0)
        current_row = default_index  # 使用传入的默认索引
        
        while True:
            draw_menu(stdscr, current_row)
            key = stdscr.getch()
            
            if key == curses.KEY_UP and current_row > 0:
                current_row -= 1
            elif key == curses.KEY_DOWN and current_row < len(options) - 1:
                current_row += 1
            elif key == ord('\n'):
                return current_row
            elif key == ord('q'):
                return -1
    
    return curses.wrapper(main)


def main():
    # 视频文件路径
    video_paths = []
    if len(sys.argv) >= 2:
        video_paths.append(sys.argv[1])
    else:
        files = []
        for dirpath, dirnames, filenames in os.walk("."):
            for filename in filenames:
                if filename.endswith(".mp4"):
                    files.append(os.path.join(dirpath, filename).replace("\\", "/"))
        
        # 使用交互式选择视频文件
        selected = select_courses_interactive(files, "选择视频文件:")
        if not selected:
            return
        for i in selected:
            video_paths.append(files[i])
        
        # 使用交互式选择模型
        models = [m for m in whisper.available_models() if ".en" not in m]
        base_index = models.index("base") if "base" in models else 0
        model_index = select_option_interactive("选择模型:", models, default_index=base_index)
        if model_index == -1:
            model_name = "base"
        else:
            model_name = models[model_index]
        print("使用模型:", model_name)

    for video_path in video_paths:
        audio_path = video_path.replace("mp4", "m4a")
        cmd = f'ffmpeg -i "{video_path}" -vn -ar {whisper.audio.SAMPLE_RATE} "{audio_path}"'
        os.system(cmd)

        model = whisper.load_model(model_name, download_root="whisper_models/")

        start = time.time()
        result = model.transcribe(audio_path, verbose=False, language="zh")
        print("Time cost: ", time.time() - start)

        # 写入字幕文件
        with open(video_path.replace("mp4", "srt"), "w", encoding="utf-8") as f:
            i = 1
            for r in result["segments"]:
                f.write(str(i) + "\n")
                f.write(
                    seconds_to_hmsm(float(r["start"]))
                    + " --> "
                    + seconds_to_hmsm(float(r["end"]))
                    + "\n"
                )
                i += 1
                f.write(
                    convert(r["text"], "zh-cn") + "\n"
                )  # 结果可能是繁体，转为简体zh-cn
                f.write("\n")

        # 删除音频文件
        os.remove(audio_path)


if __name__ == "__main__":
    main()
