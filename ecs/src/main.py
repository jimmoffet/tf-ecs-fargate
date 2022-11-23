import json
import urllib.request
import requests
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


def transcribe(url, whisper_model="base.en"):
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

    # Validate Required Environment Variable and get Metadata
    if (
        ECS_CONTAINER_METADATA_URI_V4 := os.getenv("ECS_CONTAINER_METADATA_URI_V4")
    ) is None:
        logger.error(
            "Environment Variable ECS_CONTAINER_METADATA_URI_V4 not set", fatal=True
        )
    try:
        r = requests.get(ECS_CONTAINER_METADATA_URI_V4 + "/task")
        metadata = r.json()
    except Exception as e:
        logger.error("failed to parse metadata response with error: {e}", fatal=True)

    task_arn = metadata["TaskARN"]
    # ARN is "arn:partition:service:region", so we need 4th element, i.e. 3 zero-indexed
    task_id = task_arn.split("/")[-1]
    region = task_arn.split(":")[3]
    ecs_cluster = metadata["Cluster"]

    upload_file_s3(
        input_filename,
        WHISPER_INCOMING_AUDIO_BUCKET,
        object_name=ENV_NAME + "/" + task_id + "." + filetype,
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
    logger.info(f"dict result is {result}")

    output_filename = "output.txt"
    text_file = open(output_filename, "w")
    output_str = ""
    for segment in result["segments"]:
        logger.info(f"saving a segment to output file")
        output_str += segment["text"] + "\n>"
    text_file.write(output_str)
    logger.info(f"wrote output file")
    text_file.close()

    upload_file_s3(
        output_filename,
        WHISPER_OUTGOING_TEXT_BUCKET,
        object_name=ENV_NAME + "/" + task_id + ".txt",
    )

    return json.dumps(result, indent=4)


logger.info(f"port is: {PORT}")
if __name__ == "__main__":
    try:
        result_json = transcribe(sys.argv[1], whisper_model="base.en")
        logger.debug(f"{result_json}\n")
        result_dict = json.loads(result_json)
        logger.info(f'{result_dict["text"]}')
    except Exception as e:
        logger.error(f"Main error: {e}")
        # make sure container always exits cleanly, else fargate will retry forever
        pass
