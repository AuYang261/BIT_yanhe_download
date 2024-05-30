# coding=utf-8

import os
import re
import sys
import queue
import base64
import platform
import requests
import urllib3
import time
import signal
from concurrent.futures import ThreadPoolExecutor

import utils


class ThreadPoolExecutorWithQueueSizeLimit(ThreadPoolExecutor):
    """
    实现多线程有界队列
    队列数为线程数的2倍
    """

    def __init__(self, max_workers=None, *args, **kwargs):
        super().__init__(max_workers, *args, **kwargs)
        self._work_queue = queue.Queue(max_workers * 2)


def make_sum():
    ts_num = 0
    while True:
        yield ts_num
        ts_num += 1


def dummy_func(downloaded, total, merge_status):
    return


class M3u8Download:
    """
    :param url: 完整的m3u8文件链接 如"https://www.bilibili.com/example/index.m3u8"
    :param name: 保存m3u8的文件名 如"index"
    :param max_workers: 多线程最大线程数
    :param num_retries: 重试次数
    :param base64_key: base64编码的字符串
    """

    def __init__(
        self,
        url,
        workDir,
        name,
        max_workers=32,
        num_retries=999,
        base64_key=None,
        progress_callback=dummy_func,
    ):

        self._url = url
        self._token = None
        self._workDir = workDir
        self._name = name
        self._max_workers = max_workers
        self._num_retries = num_retries
        self._progress_callback = progress_callback
        if not os.path.exists(os.path.join(os.getcwd(), self._workDir)):
            os.makedirs(os.path.join(os.getcwd(), self._workDir))
        self._file_path = os.path.join(os.getcwd(), self._workDir, self._name)
        if os.path.exists(self._file_path + ".mp4"):
            print(f"File '{self._file_path}.mp4' already exists, skip download")
            self._progress_callback(100, 100, 2)
            return
        self._front_url = None
        self._ts_url_list = []
        self._success_sum = 0
        self._ts_sum = 0
        self._key = base64.b64decode(base64_key.encode()) if base64_key else None
        self._headers = {
            "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/93.0.4577.82 Safari/537.36 Edg/93.0.961.52",
            "Origin": "https://www.yanhekt.cn",
            "referer": "https://www.yanhekt.cn/",
        }
        self.timestamp, self.signature = utils.getSignature()
        urllib3.disable_warnings()

        self._url = utils.encryptURL(self._url)

        self.get_m3u8_info(self._url, self._num_retries)

        def signal_handler(sig, frame):
            print("Caught KeyboardInterrupt. Shutting down...")
            os._exit(1)

        signal.signal(signal.SIGINT, signal_handler)
        print(
            "Downloading: %s" % self._name, "Save path: %s" % self._file_path, sep="\n"
        )
        with ThreadPoolExecutorWithQueueSizeLimit(self._max_workers) as pool:
            pool.submit(self.updateSignatureLoop)
            for k, ts_url in enumerate(self._ts_url_list):
                pool.submit(
                    self.download_ts,
                    ts_url,
                    os.path.join(self._file_path, str(k)),
                    self._num_retries,
                )
        if self._success_sum == self._ts_sum:
            self._progress_callback(self._success_sum, self._ts_sum, 1)
            self.output_mp4()
            self.delete_file()
            print(f"Download successfully --> {self._name}")
            self._progress_callback(self._success_sum, self._ts_sum, 2)

    def updateSignatureLoop(self):
        while self._success_sum != self._ts_sum:
            self.timestamp, self.signature = utils.getSignature()
            time.sleep(10)

    def get_m3u8_info(self, m3u8_url, num_retries):
        """
        获取m3u8信息
        """

        if not self._token:
            self._token = utils.getToken()
        token = self._token
        url = utils.add_signature_for_url(
            m3u8_url, token, self.timestamp, self.signature
        )
        try:
            with requests.get(
                url, timeout=(3, 30), verify=False, headers=self._headers
            ) as res:
                self._front_url = res.url.split(res.request.path_url)[0]
                if "EXT-X-STREAM-INF" in res.text:  # 判定为顶级M3U8文件
                    for line in res.text.split("\n"):
                        if "#" in line:
                            continue
                        elif line.startswith("http"):
                            self._url = line
                        elif line.startswith("/"):
                            self._url = self._front_url + line
                        else:
                            self._url = self._url.rsplit("/", 1)[0] + "/" + line
                    self.get_m3u8_info(self._url, self._num_retries)
                else:
                    m3u8_text_str = res.text
                    self.get_ts_url(m3u8_text_str)
        except Exception as e:
            print(e)
            if num_retries > 0:
                self.get_m3u8_info(m3u8_url, num_retries - 1)

    def get_ts_url(self, m3u8_text_str):
        """
        获取每一个ts文件的链接
        """
        if not os.path.exists(self._file_path):
            os.mkdir(self._file_path)
        new_m3u8_str = ""
        ts = make_sum()
        for line in m3u8_text_str.split("\n"):
            if "#" in line:
                if "EXT-X-KEY" in line and "URI=" in line:
                    if os.path.exists(os.path.join(self._file_path, "key")):
                        continue
                    key = self.download_key(line, 5)
                    if key:
                        new_m3u8_str += f"{key}\n"
                        continue
                new_m3u8_str += f"{line}\n"
                if "EXT-X-ENDLIST" in line:
                    break
            else:
                if line.startswith("http"):
                    self._ts_url_list.append(line)
                elif line.startswith("/"):
                    self._ts_url_list.append(self._front_url + line)
                else:
                    self._ts_url_list.append(self._url.rsplit("/", 1)[0] + "/" + line)
                new_m3u8_str += os.path.join(self._file_path, str(next(ts))) + "\n"
        self._ts_sum = next(ts)
        with open(self._file_path + ".m3u8", "wb") as f:
            if platform.system() == "Windows":
                # f.write(new_m3u8_str.encode('gbk'))
                f.write(new_m3u8_str.encode("utf-8"))
            else:
                f.write(new_m3u8_str.encode("utf-8"))

    def download_ts(self, ts_url, name, num_retries):
        """
        下载 .ts 文件
        """
        if not self._token:
            self._token = utils.getToken()
        token = self._token
        ts_url = utils.add_signature_for_url(
            ts_url.split("\n")[0], token, self.timestamp, self.signature
        )
        try:
            if not os.path.exists(name):
                with requests.get(
                    ts_url,
                    stream=True,
                    timeout=(5, 60),
                    verify=False,
                    headers=self._headers,
                ) as res:
                    if res.status_code == 200:
                        with open(name, "wb") as ts:
                            for chunk in res.iter_content(chunk_size=1024):
                                if chunk:
                                    ts.write(chunk)
                        self._success_sum += 1
                        sys.stdout.write(
                            "\r[%-25s](%d/%d)"
                            % (
                                "*" * (100 * self._success_sum // self._ts_sum // 4),
                                self._success_sum,
                                self._ts_sum,
                            )
                        )
                        sys.stdout.flush()
                    else:
                        self.download_ts(ts_url, name, num_retries - 1)
            else:
                self._success_sum += 1

            self._progress_callback(self._success_sum, self._ts_sum, 0)
        except Exception as e:
            if os.path.exists(name):
                os.remove(name)
            if num_retries > 0:
                self.download_ts(ts_url, name, num_retries - 1)

    def download_key(self, key_line, num_retries):
        """
        下载key文件
        """
        mid_part = re.search(r"URI=[\'|\"].*?[\'|\"]", key_line).group()
        may_key_url = mid_part[5:-1]
        if self._key:
            with open(os.path.join(self._file_path, "key"), "wb") as f:
                f.write(self._key)
            return f'{key_line.split(mid_part)[0]}URI="./{self._name}/key"'
        if may_key_url.startswith("http"):
            true_key_url = may_key_url
        elif may_key_url.startswith("/"):
            true_key_url = self._front_url + may_key_url
        else:
            true_key_url = self._url.rsplit("/", 1)[0] + "/" + may_key_url
        try:
            with requests.get(
                true_key_url, timeout=(5, 30), verify=False, headers=self._headers
            ) as res:
                with open(os.path.join(self._file_path, "key"), "wb") as f:
                    f.write(res.content)
            return f'{key_line.split(mid_part)[0]}URI="./{self._name}/key"{key_line.split(mid_part)[-1]}'
        except Exception as e:
            print(e)
            if os.path.exists(os.path.join(self._file_path, "key")):
                os.remove(os.path.join(self._file_path, "key"))
            print("加密视频,无法加载key,解密失败")
            if num_retries > 0:
                self.download_key(key_line, num_retries - 1)

    def output_mp4(self):
        """
        合并.ts文件，输出mp4格式视频，需要ffmpeg
        """
        cmd = f'''ffmpeg -allowed_extensions ALL -i "{self._file_path}.m3u8" -acodec \
        copy -vcodec copy -f mp4 "{self._file_path}.mp4"'''
        # print(cmd)
        os.system(cmd)

    def delete_file(self):
        file = os.listdir(self._file_path)
        for item in file:
            os.remove(os.path.join(self._file_path, item))
        os.removedirs(self._file_path)
        os.remove(self._file_path + ".m3u8")
