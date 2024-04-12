import curses
import utils
import m3u8dl

videoList = []
courseName = ""
professor = ""
selected_videos = []
selected_signal = []


class Row:
    def __init__(self, text, highlighted=False):
        self.text = text
        self.highlighted = highlighted


def draw_menu(stdscr, options, checked, title, current_row):
    stdscr.clear()
    height, width = stdscr.getmaxyx()
    stdscr.addnstr(0, 0, title, width // 2)
    msg = []
    for idx, option in enumerate(options):
        checkmark = "[X]" if checked[idx] else "[ ]"
        msg.append(Row(f"{checkmark} {option}", idx == current_row))
    draw_multi_select(stdscr, msg, current_row)
    stdscr.addnstr(
        height - 1,
        0,
        "按上下键移动，按空格键选择/取消选择，按回车键确认，按q键退出",
        width // 2,
    )
    stdscr.refresh()


def draw_multi_select(stdscr, messages: list, center_row):
    # 获取屏幕的行数和列数
    height, width = stdscr.getmaxyx()

    # 计算消息的开始位置以使其居中
    total_messages = len(messages)
    visible_messages = min(height - 4, total_messages)  # 屏幕可以显示的最大消息数
    start_row = max(2, (height // 2) - (visible_messages // 2))

    # 确定要显示的消息的范围
    start_index = min(
        max(0, center_row - (visible_messages // 2)), total_messages - visible_messages
    )
    end_index = min(total_messages, start_index + visible_messages)

    for i in range(start_index, end_index):
        message = messages[i]
        row = start_row + (i - start_index)
        text = message.text
        if len(text) > width:
            text = text[:width]  # 截断文本以适应屏幕宽度

        if message.highlighted:
            stdscr.attron(curses.A_REVERSE)
            stdscr.addstr(row, (width - len(text)) // 2, text)  # 居中显示文本
            stdscr.attroff(curses.A_REVERSE)
        else:
            stdscr.addstr(row, (width - len(text)) // 2, text)  # 居中显示文本


def multi_select(stdscr, options, title):
    curses.curs_set(0)  # 隐藏光标
    checked = [False] * len(options)
    current_row = 0
    while True:
        draw_menu(stdscr, options, checked, title, current_row)
        key = stdscr.getch()

        if key == curses.KEY_DOWN:
            current_row = (current_row + 1) % len(options)  # 向下循环移动
        elif key == curses.KEY_UP:
            current_row = (current_row - 1) % len(options)  # 向上循环移动
        elif key == ord("q"):
            exit()  # 退出程序
        elif key == ord(" "):
            checked[current_row] = not checked[current_row]  # 切换当前行的勾选状态
        elif key == curses.KEY_ENTER or key in [10, 13]:
            break

    # 获取选择
    return [i for i, c in enumerate(checked) if c]


def config(stdscr):
    global videoList, courseName, professor, selected_videos, selected_signal

    # 开启回显
    curses.echo()

    # 提示用户输入
    url_base = "https://www.yanhekt.cn/course/"
    while True:
        # 清除屏幕
        stdscr.clear()
        stdscr.addstr(f"(按q键退出)\n\n")
        stdscr.addstr(f"请输入课程编号: {url_base}")

        key = stdscr.getch()
        if key == ord("q"):
            exit()
        elif key != 10:
            break

    # 等待用户输入字符串并显示它
    courseID = chr(key).encode() + stdscr.getstr()
    # courseID = b"45497"
    videoList, courseName, professor = utils.get_course_info(
        courseID=courseID.decode("utf-8")
    )

    # videoList = [{"title": str(i)} for i in range(10)]

    selected_videos = []

    while True:
        selected_videos = multi_select(
            stdscr,
            [v["title"] for v in videoList],
            f"课程名：{courseName}，请选择要下载的视频:",
        )
        if not selected_videos:
            stdscr.clear()
            stdscr.addstr("请至少选择一个视频，按回车继续")
            stdscr.getch()
        else:
            break

    # 清除屏幕并显示输入的内容
    prompt = ["已选择以下视频：\n"]
    for index in selected_videos:
        prompt.append(f"{videoList[index]['title']}\n")

    selected_signal = []

    while True:
        selected_signal = multi_select(
            stdscr, ["摄像头", "电脑屏幕"], "选择要下载的信号："
        )
        if not selected_signal:
            stdscr.clear()
            stdscr.addstr("请至少选择一个信号，按回车继续")
            stdscr.getch()
        else:
            break

    stdscr.clear()


def main():
    while True:
        curses.wrapper(config)

        for i in selected_videos:
            c = videoList[i]
            name = courseName + "-" + professor + "-" + c["title"]
            print(name)
            try:
                if 1 in selected_signal:
                    m3u8dl.M3u8Download(
                        c["videos"][0]["vga"],
                        "output/" + courseName + "-screen",
                        name,
                    )
                if 0 in selected_signal:
                    m3u8dl.M3u8Download(
                        c["videos"][0]["main"],
                        "output/" + courseName + "-video",
                        name,
                    )
            except Exception as e:
                print(e)
                exit()


if __name__ == "__main__":
    main()
