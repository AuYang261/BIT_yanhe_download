import requests
import m3u8dl
import sys
import json
headers={
'Origin': 'https://www.yanhekt.cn',
"xdomain-client": "web_user",
'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/107.0.0.0 Safari/537.36 Edg/107.0.1418.26'
}


# courseID = 31425
if __name__ == '__main__':
	courseID = sys.argv[1]

	course = requests.get(f'https://cbiz.yanhekt.cn/v1/course?id={courseID}&with_professor_badges=true', headers=headers)
	req = requests.get(f'https://cbiz.yanhekt.cn/v2/course/session/list?course_id={courseID}', headers=headers)
	print(course.json()['data']['name_zh'])
	videoList = req.json()['data']
	# print(json.dumps(videoList, indent=2))
	for i, c in enumerate(videoList):
		print(i, c['title'])

	index = eval('[' + input('select(split by \',\'):') + ']')
	vga = input('video(1) or vga(2)?(input 1 or 2, default 1):')
	for i in index:
		c = videoList[i]
		name = course.json()['data']['name_zh'] + '-' + course.json()['data']['professors'][0]['name'] + '-' + c['title']
		print(name)
		if vga == "2":
			m3u8dl.M3u8Download(c['videos'][0]['vga'], course.json()['data']['name_zh'] + ('-vga' if vga == '2' else '-video'), name)
		else:
			m3u8dl.M3u8Download(c['videos'][0]['main'], course.json()['data']['name_zh'] + ('-vga' if vga == '2' else '-video'), name)


