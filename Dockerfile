FROM python:3-alpine

RUN pip install watson_developer_cloud==0.26.0 slackclient

RUN mkdir -p /app/iobot

ADD 100bot.py /app/iobot/100bot.py

ENTRYPOINT ["python3", "/app/iobot/100bot.py"]
