import json
import urllib.request
import os
import logging
import sys
import pickle
import whisper
from utils import upload_file_s3, get_file_type, stripAudioFromVideo


# Setup logging in order for CloudWatch Logs to work properly
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger()

PORT = os.getenv("PORT", "you-forget-to-set-port-env")
WHISPER_INCOMING_AUDIO_BUCKET = os.getenv(
    "WHISPER_INCOMING_AUDIO_BUCKET",
    "you-forget-to-set-whisper-incoming-audio-bucket-env",
)
WHISPER_OUTGOING_TEXT_BUCKET = os.getenv(
    "WHISPER_OUTGOING_TEXT_BUCKET", "you-forget-to-set-whisper-outgoing-text-bucket-env"
)
ENV_NAME = os.getenv("ENV_NAME", "you-forget-to-set-env-name-env")


def transcribe(url, job_id, whisper_model="base.en"):
    """Transcribe audio file from url
    base.en is the default model, ~300mb
    small.en is a somewhat larger model, ~1gb
    medium.en is the largest english-only model, ~5gb
    """

    input_filename = "processed"
    processed_filename = "processed.mp3"
    urllib.request.urlretrieve(url, input_filename)
    logger.info(f"Audio has been downloaded to file {input_filename}")

    filetype = "mp3"

    filetype, mimetype = get_file_type(input_filename)
    if "video" in mimetype:
        logger.info(f"Detected video filetype: {filetype}")
        stripAudioFromVideo(input_filename, processed_filename)
        input_filename = processed_filename
    elif "audio" in mimetype:
        logger.info(f"Detected audio filetype: {filetype}")
        input_filename = input_filename
    else:
        logger.info(f"Detected unknown filetype: {filetype}")
        stripAudioFromVideo(input_filename, processed_filename)
        input_filename = processed_filename
        logger.info(f"input filename is now: {input_filename}")
    # TODO: probably abort if filetype is not found

    upload_file_s3(
        input_filename,
        WHISPER_INCOMING_AUDIO_BUCKET,
        object_name=ENV_NAME + "/" + job_id + "." + filetype,
    )

    model_file = whisper_model + ".pickle"
    if not os.path.exists(model_file):
        logger.info(f"pickled model not found, downloading now")
        model_object = whisper.load_model(whisper_model)
        with open(model_file, "wb") as handle:
            pickle.dump(model_object, handle, protocol=pickle.HIGHEST_PROTOCOL)

    with open(model_file, "rb") as handle:
        logger.info(f"loading model from local file")
        model = pickle.load(handle)

    result = model.transcribe(input_filename)
    logger.debug(f"dict result is {result}")

    output_filename = "output.txt"
    text_file = open(output_filename, "w")
    output_str = ""
    for segment in result["segments"]:
        logger.debug(f"saving a segment to output file")
        output_str += segment["text"] + "\n>"
    text_file.write(output_str)
    logger.debug(f"wrote output file")
    text_file.close()

    upload_file_s3(
        output_filename,
        WHISPER_OUTGOING_TEXT_BUCKET,
        object_name=ENV_NAME + "/" + job_id + ".txt",
    )

    # we'll need an input lambda to receive a POST with audio url, which will send the audio url and a unique id to the fargate task, fargate creates the txt file with the id, lambda returns the id to the requester. The requester can then poll the lambda with the id to get the txt file once it becomes available. Fargate could write an error to the beginning of the file if it fails, and the lambda could check for that and return an error to the requester.

    return json.dumps(result, indent=4)


logger.info(f"port is: {PORT}")
if __name__ == "__main__":
    result_json = transcribe(sys.argv[1], sys.argv[2], whisper_model="base.en")
    logger.debug(f"{result_json}\n")
    result_dict = json.loads(result_json)
    logger.info(f'{result_dict["text"]}')
