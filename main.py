# coding=utf-8

import requests
import m3u8dl
import sys
import json
import os
import cProfile
import time
import utils

headers = {
    "Origin": "https://www.yanhekt.cn",
    "xdomain-client": "web_user",
    "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/107.0.0.0 Safari/537.36 Edg/107.0.1418.26",
}


# courseID = 31425
def main():
    if len(sys.argv) == 1:
        courseID = input("输 入 课 程 ID: ")
    else:
        courseID = sys.argv[1]

    videoList, courseName, professor = utils.get_course_info(courseID=courseID)
    # course = requests.get(
    #     f"https://cbiz.yanhekt.cn/v1/course?id={courseID}&with_professor_badges=true",
    #     headers=headers,
    # )
    # req = requests.get(
    #     f"https://cbiz.yanhekt.cn/v2/course/session/list?course_id={courseID}",
    #     headers=headers,
    # )
    # if course.json()["code"] != "0" and course.json()["code"] != 0:
    #     print(course.json()["code"])
    #     print(course.json()["message"])
    #     raise Exception(
    #         "Please Check your course ID, note that it should be started with yanhekt.cn/course/***, not yanhekt.cn/session/***"
    #     )
    # print(course.json()["data"]["name_zh"])
    # videoList = req.json()["data"]
    # print(json.dumps(videoList, indent=2))
    for i, c in enumerate(videoList):
        print(f"[{i}]: ", c["title"])

    index = eval(
        "[" + input("选择课程编号(用 英 文 逗 号 ','分 隔, 例 如: 0,2,4): ") + "]"
    )
    vga = input(
        "选 择 下 载 摄 像 头 (1) 还 是 电 脑 屏 幕(2)?(输 入 1 或 2, 默 认 摄 像 头):"
    )
    if not os.path.exists("output/"):
        os.mkdir("output/")
    for i in index:
        c = videoList[i]
        name = courseName + "-" + professor + "-" + c["title"]
        print(name)
        if vga == "2":
            print("Downloading screen...")
            m3u8dl.M3u8Download(
                c["videos"][0]["vga"],
                "output/" + courseName + "-screen",
                name,
            )
        else:
            print("Downloading video...")
            m3u8dl.M3u8Download(
                c["videos"][0]["main"],
                "output/" + courseName + "-video",
                name,
            )


if __name__ == "__main__":
    try:
        main()
        # cProfile.run('main()', 'output/profile.txt')
    except Exception as e:
        print(e)
        print(
            "If the problem is still not solved, you can report an issue in https://github.com/AuYang261/BIT_yanhe_download/issues."
        )
        print("Or contact with the author xu_jyang@163.com. Thanks for your report!")
        print(
            "如果问题仍未解决，您可以在https://github.com/AuYang261/BIT_yanhe_download/issues 中报告问题。"
        )
        print("或者联系作者xu_jyang@163.com。感谢您的报告！")
