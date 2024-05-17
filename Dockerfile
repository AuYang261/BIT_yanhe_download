FROM python:3.8-slim

WORKDIR /app

# 创建新的sources.list
RUN echo "deb http://mirrors.ustc.edu.cn/debian/ buster main contrib non-free" > /etc/apt/sources.list && \
    echo "deb http://mirrors.ustc.edu.cn/debian/ buster-updates main contrib non-free" >> /etc/apt/sources.list && \
    echo "deb http://mirrors.ustc.edu.cn/debian-security buster/updates main contrib non-free" >> /etc/apt/sources.list


RUN apt-get update && \
  apt-get install -y ffmpeg && \
  rm -rf /var/lib/apt/lists/*

COPY . /app


RUN pip install Flask requests

EXPOSE 5001

VOLUME /app/output

CMD ["python", "webui_interface.py"]