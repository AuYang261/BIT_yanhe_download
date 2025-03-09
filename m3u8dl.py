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
        num_retries=99,
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
                    k,
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
                if res.status_code != 200:
                    raise Exception(f"Failed to get m3u8 info: {res.status_code}")
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
        new_m3u8_str = "#EXTM3U\n#EXT-X-VERSION:3\n"  # 确保包含必要的头信息
        ts = make_sum()
        duration_line = ""
        for line in m3u8_text_str.split("\n"):
            if "#" in line:
                if "EXT-X-KEY" in line and "URI=" in line:
                    if os.path.exists(os.path.join(self._file_path, "key")):
                        continue
                    key = self.download_key(line, 5)
                    if key:
                        new_m3u8_str += f"{key}\n"
                        continue
                # 保存EXTINF行（包含时长信息）
                if "EXTINF" in line:
                    duration_line = line
                    continue
                new_m3u8_str += f"{line}\n"
                if "EXT-X-ENDLIST" in line:
                    break
            else:
                if line and line.strip():  # 确保行不是空的
                    if line.startswith("http"):
                        self._ts_url_list.append(line)
                    elif line.startswith("/"):
                        self._ts_url_list.append(self._front_url + line)
                    else:
                        self._ts_url_list.append(self._url.rsplit("/", 1)[0] + "/" + line)
                    
                    ts_index = next(ts)
                    if duration_line:
                        new_m3u8_str += f"{duration_line}\n"  # 添加时长信息行
                        duration_line = ""
                    
                    # 使用.ts扩展名保存文件
                    ts_file = str(ts_index) + ".ts"
                    ts_path = os.path.join(self._file_path, ts_file).replace('\\', '/')
                    # 在m3u8文件中使用相对路径
                    rel_path = os.path.basename(self._file_path) + "/" + ts_file
                    new_m3u8_str += f"{rel_path}\n"
        
        self._ts_sum = next(ts)
        # 确保m3u8文件以EXT-X-ENDLIST结尾
        if not new_m3u8_str.strip().endswith("EXT-X-ENDLIST"):
            new_m3u8_str += "#EXT-X-ENDLIST\n"
            
        m3u8_file_path = self._file_path + ".m3u8"
        with open(m3u8_file_path, "wb") as f:
            if platform.system() == "Windows":
                # f.write(new_m3u8_str.encode('gbk'))
                f.write(new_m3u8_str.encode("utf-8"))
            else:
                f.write(new_m3u8_str.encode("utf-8"))
        
        print(f"已生成m3u8文件: {m3u8_file_path}")

    def download_ts(self, ts_url_original, index, num_retries):
        """
        下载 .ts 文件
        """
        # 确保index是数字，用于文件命名
        if isinstance(index, str) and index.endswith('.ts'):
            index = index.rstrip('.ts')
        
        # 构建TS文件路径
        ts_file = os.path.join(self._file_path, f"{index}.ts")
        
        if not self._token:
            self._token = utils.getToken()
        token = self._token
        ts_url = utils.add_signature_for_url(
            ts_url_original.split("\n")[0], token, self.timestamp, self.signature
        )
        try:
            if not os.path.exists(ts_file):
                with requests.get(
                    ts_url,
                    stream=True,
                    timeout=(5, 60),
                    verify=False,
                    headers=self._headers,
                ) as res:
                    if res.status_code == 200:
                        with open(ts_file, "wb") as ts:
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
                        self.download_ts(ts_url_original, index, num_retries - 1)
            else:
                self._success_sum += 1

            self._progress_callback(self._success_sum, self._ts_sum, 0)
        except Exception as e:
            if os.path.exists(ts_file):
                os.remove(ts_file)
            if num_retries > 0:
                self.download_ts(ts_url_original, index, num_retries - 1)

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
        # 检查所有TS文件是否正确
        self.verify_all_ts_files()
        
        # 第一种方法：通过m3u8文件合并
        print("尝试方法1：通过m3u8文件合并...")
        cmd = f'''ffmpeg -allowed_extensions ALL -protocol_whitelist "file,http,https,tcp,tls" -i "{self._file_path}.m3u8" -acodec \
        copy -vcodec copy -bsf:a aac_adtstoasc -f mp4 "{self._file_path}.mp4"'''
        result = os.system(cmd)
        
        # 如果第一种方法失败，尝试第二种方法：直接合并TS文件
        if result != 0:
            print("方法1失败，尝试方法2：通过文件列表合并...")
            # 创建包含所有ts文件的列表文件
            ts_list_file = f"{self._file_path}_ts_list.txt"
            with open(ts_list_file, "w") as f:
                for i in range(self._ts_sum):
                    ts_file = os.path.join(self._file_path, f"{i}.ts").replace('\\', '/')
                    if os.path.exists(ts_file):
                        f.write(f"file '{ts_file}'\n")
            
            # 使用ffmpeg的concat方法直接合并
            concat_cmd = f'''ffmpeg -f concat -safe 0 -i "{ts_list_file}" -c copy "{self._file_path}.mp4"'''
            result2 = os.system(concat_cmd)
            
            # 清理临时文件
            if os.path.exists(ts_list_file):
                os.remove(ts_list_file)
                
            # 如果第二种方法也失败，尝试第三种方法：直接拼接所有TS文件
            if result2 != 0:
                print("方法2失败，尝试方法3：直接拼接TS文件...")
                # 创建一个临时文件用于存储所有合并的TS内容
                temp_ts = f"{self._file_path}_temp.ts"
                with open(temp_ts, "wb") as outfile:
                    for i in range(self._ts_sum):
                        ts_file = os.path.join(self._file_path, f"{i}.ts")
                        if os.path.exists(ts_file):
                            with open(ts_file, "rb") as infile:
                                outfile.write(infile.read())
                
                # 使用ffmpeg将合并后的TS文件转换为MP4
                os.system(f'''ffmpeg -i "{temp_ts}" -acodec copy -vcodec copy "{self._file_path}.mp4"''')
                
                # 清理临时文件
                if os.path.exists(temp_ts):
                    os.remove(temp_ts)

    def verify_all_ts_files(self):
        """
        验证所有下载的TS文件
        """
        print("验证下载的TS文件完整性...")
        fixed_count = 0
        for i in range(self._ts_sum):
            # 使用新的文件命名方式
            ts_file = os.path.join(self._file_path, f"{i}.ts")
            needs_redownload = False
            
            # 检查文件是否存在
            if not os.path.exists(ts_file):
                print(f"文件 {ts_file} 不存在，将重新下载")
                needs_redownload = True
            # 检查文件大小
            elif os.path.getsize(ts_file) < 100:  # 小于100字节的文件可能是无效的
                print(f"文件 {ts_file} 大小异常（{os.path.getsize(ts_file)}字节），将重新下载")
                needs_redownload = True
            # 检查文件内容
            else:
                try:
                    with open(ts_file, 'rb') as f:
                        header = f.read(4)
                        # 有效的TS文件通常以0x47开头
                        if len(header) > 0 and header[0] != 0x47:
                            print(f"文件 {ts_file} 内容异常，将重新下载")
                            needs_redownload = True
                except Exception as e:
                    print(f"检查文件 {ts_file} 时出错: {str(e)}，将重新下载")
                    needs_redownload = True
            
            # 重新下载文件（如果需要）
            if needs_redownload:
                if i < len(self._ts_url_list):
                    # 如果文件存在，先删除
                    if os.path.exists(ts_file):
                        os.remove(ts_file)
                    # 重新下载
                    print(f"正在重新下载片段 {i}...")
                    self.download_ts(self._ts_url_list[i], i, self._num_retries)
                    fixed_count += 1
                else:
                    print(f"无法重新下载片段 {i}，URL列表中没有对应项")
        
        if fixed_count > 0:
            print(f"共修复了 {fixed_count} 个TS文件")
        else:
            print("所有TS文件验证通过")

    def delete_file(self):
        file = os.listdir(self._file_path)
        for item in file:
            os.remove(os.path.join(self._file_path, item))
        os.removedirs(self._file_path)
        os.remove(self._file_path + ".m3u8")
