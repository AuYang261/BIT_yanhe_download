# BIT_yanghe_download

 ## 下载指定课程

打开命令行，使用如下指令将仓库克隆到本地：

```bash
git clone https://github.com/AuYang261/BIT_yanghe_download.git
```

在[延河课堂 (yanhekt.cn)](https://www.yanhekt.cn/recordCourse)中找到想下载的课程，以链接为https://www.yanhekt.cn/course/39134的课程为例，复制地址栏最后的编号39134。

在仓库目录下执行命令，将39134替换为想下载的课程编号：

```bash
python main.py 39134
```

输出课程视频列表：

![image-20230331172059079](md/README/image-20230331172059079.png)

输入想下载的视频编号，用英文逗号(,)分隔，回车。接着选择下载视频录像还是下载vga信号（即教室电脑的屏幕），默认为视频录像。回车即开始下载：

![image-20230331172319645](md/README/image-20230331172319645.png)

下载完成的文件在同级目录下以课程名-video/vga格式命名的文件夹中。

![image-20230331172530624](md/README/image-20230331172530624.png)