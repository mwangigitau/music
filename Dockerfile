FROM python:3.10.13

ENV PYTHONUNBUFFERED=1

WORKDIR /app

COPY . /app/

RUN apt-get update && \
    apt-get install -y wget && \
    pip3 install --upgrade pip && \
    pip3 install -r requirements.txt && \
    wget https://github.com/yt-dlp/yt-dlp/releases/latest/download/yt-dlp -O /usr/local/bin/yt-dlp && \
    chmod a+rx /usr/local/bin/yt-dlp

# RUN apt-get install -y ffmpeg

RUN apt-get clean && \
    rm -rf /var/lib/apt/lists/*

# CMD ["python3", "main.py"]
