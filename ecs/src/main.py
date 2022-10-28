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

# url = "https://github.com/AssemblyAI-Examples/audio-intelligence-dashboard/raw/master/gettysburg10.wav"


@app.route('/')
def transcribe(url):
    filename = "audio.wav"
    logger.debug(f"Hello world - this is fargate task endpoint /")

    urllib.request.urlretrieve(url, filename)
    logger.debug(f"Hello world - this is fargate task endpoint / downloaded")

    # SAVE AUDIO FILE TO S3 IN CASE WE NEED TO RETRY

    if not os.path.exists("base-en.pickle"):
        logger.info(f"pickled model not found")
        model_object = whisper.load_model("base.en")
        with open('base-en.pickle', 'wb') as handle:
            pickle.dump(model_object, handle, protocol=pickle.HIGHEST_PROTOCOL)

    with open('base-en.pickle', 'rb') as handle:
        logger.info(f"loading model from file")
        model = pickle.load(handle)

    result = model.transcribe(filename)
    logger.debug(f"dict result is {result}")

    text_file = open("output.txt", "w")
    output_str = ""
    for segment in result["segments"]:
        logger.debug(f"saving a segment to output file")
        output_str += segment["text"]+"\n>"
    text_file.write(output_str)
    logger.debug(f"wrote output file")
    text_file.close()

    # SAVE TXT TO S3 AND PASS VIA SNS MSG TO OUTPUT LAMBDA

    # we'll need an input lambda to receive a POST with audio url, which will send the audio url and a unique id to the fargate task, fargate creates the txt file with the id, lambda returns the id to the requester. The requester can then poll the lambda with the id to get the txt file once it becomes available. Fargate could write an error to the beginning of the file if it fails, and the lambda could check for that and return an error to the requester.

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
