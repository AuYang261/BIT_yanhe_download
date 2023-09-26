# BIT_yanhe_download

 ## 依赖

 * python第三方库： 
 ```
 requests、execjs
 ```
 * [ffmpeg](https://www.gyan.dev/ffmpeg/builds/ffmpeg-release-essentials.zip)，下载后解压，并将bin/文件夹添加到环境变量，以确保输入命令``` ffmpeg ```能输出版本信息

 ## 下载指定课程

打开命令行，使用如下指令将仓库克隆到本地：

```bash
git clone https://github.com/AuYang261/BIT_yanghe_download.git
```

在[延河课堂 (yanhekt.cn)](https://www.yanhekt.cn/recordCourse)中找到想下载的课程，以链接为https://www.yanhekt.cn/course/39134 的课程为例，复制地址栏最后的编号39134。

在仓库目录下执行命令，将39134替换为想下载的课程编号：

```bash
python main.py 39134
```

或双击运行`run.bat`文件，并输入课程编号

输出课程视频列表：

![image-20230926124749421](md/README/image-20230926124749421.png)

输入想下载的视频编号，用英文逗号(,)分隔，回车。接着选择下载video视频录像（即教室后的摄像头录像）还是下载screen信号（即教室电脑的屏幕），默认为视频录像。回车即开始下载：

![image-20230926124841432](md/README/image-20230926124841432.png)

下载完成的文件在`output/`目录下以课程名-video/screen格式命名的文件夹中。

![image-20230926124922726](md/README/image-20230926124922726.png)

## 注意

* 需要关闭本机上的代理，否则会提示类似`ValueError: check_hostname requires server_hostname`的报错信息。
