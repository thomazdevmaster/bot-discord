FROM python:3.10-slim

RUN apt-get update && apt-get install -y tzdata ffmpeg
ENV TZ=America/Sao_Paulo

RUN pip install --upgrade pip setuptools

WORKDIR /app
COPY requirements.txt requirements.txt
RUN pip install -r requirements.txt

COPY . /app
COPY ./audios /app/audios


CMD ["python", "bot.py"]