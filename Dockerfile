FROM python:3

RUN pip install watson_developer_cloud==0.26.0 slackclient

RUN mkdir -p /app/iobot

ADD Io.py /app/iobot/Io.py

ENTRYPOINT ["python3", "/app/iobot/Io.py"]
