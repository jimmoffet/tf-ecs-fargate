import json
import urllib.request
import os
import logging
import sys
import pickle
from flask import Flask
import whisper


# Setup logging in order for CloudWatch Logs to work properly
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger()

app = Flask(__name__)

url = "https://github.com/AssemblyAI-Examples/audio-intelligence-dashboard/raw/master/gettysburg10.wav"


@app.route('/')
def transcribe(url):
    filename = "audio.wav"
    logger.debug(f"Hello world - this is fargate task endpoint /")

    urllib.request.urlretrieve(url, filename)
    logger.debug(f"Hello world - this is fargate task endpoint / downloaded")

    # model = whisper.load_model("base.en")
    # with open('base-en.pickle', 'wb') as handle:
    #     pickle.dump(model, handle, protocol=pickle.HIGHEST_PROTOCOL)

    with open('base-en.pickle', 'rb') as handle:
        model = pickle.load(handle)

    result = model.transcribe(filename)
    logger.debug(f"dict result is {result}")

    text_file = open("output.txt", "w")
    for segment in result["segments"]:
        text_file.write(segment["text"])
    text_file.close()

    return json.dumps(result, indent=4)


# @app.route('/hello')
# def hello():
#     url = "https://github.com/AssemblyAI-Examples/audio-intelligence-dashboard/raw/master/gettysburg10.wav"
#     filename = "audio.wav"
#     # urllib.request.urlretrieve(url, filename)
#     # model = whisper.load_model("base")
#     # result = model.transcribe(filename)
#     # logger.info(f"result is {result}")
#     logger.info(f"Hello world - this is fargate task endpoint /hello")
#     return str("hello")


port = os.getenv('PORT', '80')
logger.debug(f"port is: {port}")
if __name__ == "__main__":
    result_json = transcribe(sys.argv[1])
    logger.debug(f"{result_json}\n")
    result_dict = json.loads(result_json)
    logger.info(f'{result_dict["text"]}')
    # app.run(host='0.0.0.0', port=int(port))
