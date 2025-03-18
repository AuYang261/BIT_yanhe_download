import os
import sys

import m3u8dl
import utils

headers = {
    "Origin": "https://www.yanhekt.cn",
    "xdomain-client": "web_user",
    "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/107.0.0.0 Safari/537.36 Edg/107.0.1418.26",
}


@utils.print_help
def main():
    if len(sys.argv) == 1:
        courseID = input("输 入 课 程 ID: ")
    else:
        courseID = sys.argv[1]

    if not utils.read_auth() or not utils.test_auth(courseID=courseID):
        auth = input("。".join(utils.auth_prompt()))
        utils.write_auth(auth)
        if not utils.test_auth(courseID=courseID):
            print("身份验证失败")
            sys.exit()
    videoList, courseName, professor = utils.get_course_info(courseID=courseID)

    print(f"课 程 名: {courseName}")

    for i, c in enumerate(videoList):
        print(f"[{i}]: ", c["title"])

    index = eval(
        "[" + input("选 择 课 程 编 号 (用 英 文 逗 号 ','分 隔, 例 如: 0,2,4): ") + "]"
    )
    vga = input(
        "选 择 下 载 摄 像 头 (1) 还 是 电 脑 屏 幕 (2)?(输 入 1 或 2, 默 认 摄 像 头):"
    )
    audio = input(
        "是 否 下 载 教 室 蓝 牙 话 筒 的 音 频 ?若 教 师 未 使 用 蓝 牙 话 筒 则 该 音 频 无 声 音 (输 入 1不 下 载, 默 认 下 载):"
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


if __name__ == "__main__":
    main()
