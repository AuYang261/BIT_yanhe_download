# coding: utf-8

import requests
import m3u8dl


def get_course_info(courseID):
    headers = {
        "Origin": "https://www.yanhekt.cn",
        "xdomain-client": "web_user",
        "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/107.0.0.0 Safari/537.36 Edg/107.0.1418.26",
    }

    course = requests.get(
        f"https://cbiz.yanhekt.cn/v1/course?id={courseID}&with_professor_badges=true",
        headers=headers,
    )
    res = requests.get(
        f"https://cbiz.yanhekt.cn/v2/course/session/list?course_id={courseID}",
        headers=headers,
    )

    if course.json()["code"] != "0" and course.json()["code"] != 0:
        # print(course.json()["code"])
        # print(course.json()["message"])
        raise Exception(
            "请检查您的课程ID，注意它应该是5位数字，从课程信息界面的链接yanhekt.cn/course/***获取，而不是课程播放界面的链接yanhekt.cn/session/***"
        )
    # print(course.json()["data"]["name_zh"])
    videoList = res.json()["data"]
    name = course.json()["data"]["name_zh"].strip()
    if not videoList:
        raise Exception(f"该课程({name})没有视频信息，请检查课程ID是否正确")

    return (
        videoList,
        name,
        (
            course.json()["data"]["professors"][0]["name"].strip()
            if course.json()["data"]["professors"]
            else "未知教师"
        ),
    )
