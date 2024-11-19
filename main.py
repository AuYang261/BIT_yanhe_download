# coding=utf-8

import requests
import m3u8dl
import sys
import json
import os
import cProfile
import time
import utils
import curses

headers = {
    "Origin": "https://www.yanhekt.cn",
    "xdomain-client": "web_user",
    "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/107.0.0.0 Safari/537.36 Edg/107.0.1418.26",
}


@utils.print_help
def main():
    if len(sys.argv) == 1:
        courseID = input("输入课程ID: ")
    else:
        courseID = sys.argv[1]

    if not utils.read_auth() or not utils.test_auth(courseID=courseID):
        auth = input("。".join(utils.auth_prompt()))
        utils.write_auth(auth)
        if not utils.test_auth(courseID=courseID):
            print("身份验证失败")
            sys.exit()
    videoList, courseName, professor = utils.get_course_info(courseID=courseID)

    index = select_courses_interactive(videoList, courseName)
    vga = select_option_interactive(
        "选择下载内容:",
        ["摄像头", "电脑屏幕"]
    )

    audio = select_option_interactive(
        "是否下载教室蓝牙话筒的音频? 若教师未使用蓝牙话筒则该音频无声音:",
        ["下载", "不下载"]
    )
    if not os.path.exists("output/"):
        os.mkdir("output/")
    for i in index:
        c = videoList[i]
        name = courseName + "-" + professor + "-" + c["title"]
        print(name)
        if vga == "2":
            path = f"output/{courseName}-screen"
            print("Downloading screen...")
            m3u8dl.M3u8Download(c["videos"][0]["vga"], path, name)
        else:
            path = f"output/{courseName}-video"
            print("Downloading video...")
            m3u8dl.M3u8Download(c["videos"][0]["main"], path, name)
        if audio == "" and c["video_ids"]:
            audio_url = utils.get_audio_url(c["video_ids"][0])
            if audio_url:
                print("Downloading audio...")
                utils.download_audio(audio_url, path, name)
                print("Download audio successfully.")


def select_courses_interactive(videoList, courseName):
    """使用光标交互式选择课程"""
    def draw_menu(stdscr, current_row, selected):
        stdscr.clear()
        h, w = stdscr.getmaxyx()
        
        # 显示课程名和操作说明
        stdscr.addstr(0, 0, f"课程名: {courseName}")
        stdscr.addstr(1, 0, "使用↑↓键移动, 回车选择/取消, y确认, q退出")
        stdscr.addstr(2, 0, "-" * (w-1))
        
        # 显示课程列表
        for idx, course in enumerate(videoList):
            y = idx + 4  # 从第4行开始显示课程列表
            if y >= h:
                break
                
            mark = "[*]" if idx in selected else "[ ]"
            text = f"{mark} [{idx}]: {course['title']}"
            
            if idx == current_row:
                stdscr.attron(curses.A_REVERSE)
                stdscr.addstr(y, 0, text[:w-1])
                stdscr.attroff(curses.A_REVERSE)
            else:
                stdscr.addstr(y, 0, text[:w-1])
        
        stdscr.refresh()

    def main(stdscr):
        # 设置光标不可见
        curses.curs_set(0)
        
        current_row = 0
        selected = []
        
        while True:
            draw_menu(stdscr, current_row, selected)
            
            # 获取用户输入
            key = stdscr.getch()
            
            if key == curses.KEY_UP and current_row > 0:
                current_row -= 1
            elif key == curses.KEY_DOWN and current_row < len(videoList) - 1:
                current_row += 1
            elif key == ord('\n'):  # 回车键
                if current_row in selected:
                    selected.remove(current_row)
                else:
                    selected.append(current_row)
            elif key == ord('y'):  # y键确认
                if selected:
                    return selected
            elif key == ord('q'):  # q键退出
                return []
    
    # 运行curses程序
    return curses.wrapper(main)


def select_option_interactive(title, options):
    """通用的交互式单选菜单"""
    def draw_menu(stdscr, current_row):
        stdscr.clear()
        h, w = stdscr.getmaxyx()
        
        # 显示标题和操作说明
        stdscr.addstr(0, 0, title)
        stdscr.addstr(1, 0, "使用↑↓键移动, 回车选择, q退出")
        stdscr.addstr(2, 0, "-" * (w-1))
        
        # 显示选项
        for idx, option in enumerate(options):
            y = idx + 4
            if y >= h:
                break
                
            if idx == current_row:
                stdscr.attron(curses.A_REVERSE)
                stdscr.addstr(y, 0, f"[{idx + 1}] {option}")
                stdscr.attroff(curses.A_REVERSE)
            else:
                stdscr.addstr(y, 0, f"[{idx + 1}] {option}")
        
        stdscr.refresh()

    def main(stdscr):
        curses.curs_set(0)
        current_row = 0
        
        while True:
            draw_menu(stdscr, current_row)
            key = stdscr.getch()
            
            if key == curses.KEY_UP and current_row > 0:
                current_row -= 1
            elif key == curses.KEY_DOWN and current_row < len(options) - 1:
                current_row += 1
            elif key == ord('\n'):  # 回车选择
                return str(current_row + 1)
            elif key == ord('q'):  # q键选择默认选项
                return ""
    
    return curses.wrapper(main)


if __name__ == "__main__":
    main()
