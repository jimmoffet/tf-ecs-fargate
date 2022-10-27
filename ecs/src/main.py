import json
import urllib.request
import os
import logging
from flask import Flask
import whisper
import pickle


# Setup logging in order for CloudWatch Logs to work properly
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger()

app = Flask(__name__)


@app.route('/')
def yo():
    url = "https://github.com/AssemblyAI-Examples/audio-intelligence-dashboard/raw/master/gettysburg10.wav"
    filename = "audio.wav"
    logger.debug(f"Hello world - this is fargate task endpoint /")
    urllib.request.urlretrieve(url, filename)
    logger.debug(f"Hello world - this is fargate task endpoint / downloaded")
    model = whisper.load_model("base.en")

    with open('filename.pickle', 'wb') as handle:
        pickle.dump(model, handle, protocol=pickle.HIGHEST_PROTOCOL)

    with open('filename.pickle', 'rb') as handle:
        model = pickle.load(handle)

    result = model.transcribe(filename)
    logger.debug(f"result is {result}")
    logger.debug(f"Hello world - this is fargate task endpoint / transcribed")
    return str(result)


@app.route('/hello')
def hello():
    url = "https://github.com/AssemblyAI-Examples/audio-intelligence-dashboard/raw/master/gettysburg10.wav"
    filename = "audio.wav"
    # urllib.request.urlretrieve(url, filename)
    # model = whisper.load_model("base")
    # result = model.transcribe(filename)
    # logger.info(f"result is {result}")
    logger.info(f"Hello world - this is fargate task endpoint /hello")
    return str("hello")


port = os.getenv('PORT', '80')
logger.info(f"port is: {port}")
if __name__ == "__main__":
    result = yo()
    logger.info(f"{result}")
    logger.info(f'{result["text"]}')
    # app.run(host='0.0.0.0', port=int(port))
