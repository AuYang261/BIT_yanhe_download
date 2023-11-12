import requests
import m3u8dl
import sys
import json
import os
import cProfile
headers={
    'Origin': 'https://www.yanhekt.cn',
    "xdomain-client": "web_user",
    'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/107.0.0.0 Safari/537.36 Edg/107.0.1418.26'
}


# courseID = 31425
def main():
    if len(sys.argv) == 1:
        courseID = eval(input('Please input course ID: '))
    else:
        courseID = sys.argv[1]

    course = requests.get(f'https://cbiz.yanhekt.cn/v1/course?id={courseID}&with_professor_badges=true', headers=headers)
    req = requests.get(f'https://cbiz.yanhekt.cn/v2/course/session/list?course_id={courseID}', headers=headers)
    if course.json()['code'] != '0' and course.json()['code'] != 0:
        print(course.json()['code'])
        print(course.json()['message'])
        raise Exception("Please Check your course ID, note that it should be started with yanhekt.cn/course/***, not yanhekt.cn/session/***")
    print(course.json()['data']['name_zh'])
    videoList = req.json()['data']
    # print(json.dumps(videoList, indent=2))
    for i, c in enumerate(videoList):
        print(i, c['title'])

    index = eval('[' + input('select(split by \',\'):') + ']')
    vga = input('video(1) or screen(2)?(input 1 or 2, default 1):')
    if not os.path.exists('output/'):
        os.mkdir('output/')
    for i in index:
        c = videoList[i]
        name = course.json()['data']['name_zh'].strip() + '-' + course.json()['data']['professors'][0]['name'] + '-' + c['title']
        print(name)
        if vga == "2":
            print("Downloading screen...")
            m3u8dl.M3u8Download(c['videos'][0]['vga'], 'output\\' + course.json()['data']['name_zh'].strip() + ('-screen' if vga == '2' else '-video'), name)
        else:
            print("Downloading video...")
            m3u8dl.M3u8Download(c['videos'][0]['main'], 'output\\'+ course.json()['data']['name_zh'].strip() + ('-screen' if vga == '2' else '-video'), name)


if __name__ == '__main__':
    try:
        # main()
        cProfile.run('main()', 'profile.txt')
    except Exception as e:
        print(e)
        print("If the problem is still not solved, you can report an issue in https://github.com/AuYang261/BIT_yanhe_download/issues.")
        print("Or contact with the author xu_jyang@163.com. Thanks for your report!")
