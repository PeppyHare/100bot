FROM python:3-alpine

RUN pip install slackclient requests

RUN mkdir -p /app/iobot

ADD 100bot.py /app/iobot/100bot.py

ENTRYPOINT ["python3", "/app/iobot/100bot.py"]
