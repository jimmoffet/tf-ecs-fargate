FROM python:3.9-slim
RUN apt-get update && apt-get install -y git ffmpeg
RUN mkdir /src
ADD requirements.txt /src/requirements.txt
RUN python3.9 -m pip install -r /src/requirements.txt
ADD main.py /src/main.py
WORKDIR /src
ENTRYPOINT ["python", "main.py"]
