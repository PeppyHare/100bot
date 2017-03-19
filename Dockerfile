FROM python:3-alpine

RUN pip install watson_developer_cloud slackclient

RUN mkdir -p /app/iobot

ADD Io.py /app/iobot/Io.py

ENTRYPOINT ["python3", "/app/iobot/Io.py"]
