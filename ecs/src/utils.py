import os
import logging
import boto3
from botocore.exceptions import ClientError
import filetype

# Setup logging in order for CloudWatch Logs to work properly
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger()


def upload_file_s3(file_name, bucket, object_name=None):
    """Upload a file to an S3 bucket
    :param file_name: File to upload
    :param bucket: Bucket to upload to
    :param object_name: S3 object name. If not specified then file_name is used
    :return: True if file was uploaded, else False
    """
    if object_name is None:
        object_name = os.path.basename(file_name)

    s3_client = boto3.client("s3")
    try:
        response = s3_client.upload_file(file_name, bucket, object_name)
    except ClientError as e:
        logging.error(e)
        return False
    return True


def get_file_type(filename):
    """Get the file type of a file
    :param filename: File to get the type of
    :return: File type
    """
    kind = filetype.guess(filename)
    if kind is None:
        logger.info(f"Cannot guess file type!")
        return "unknown", "unknown"

    logger.info(f"File extension: {kind.extension}")
    logger.info(f"File mimetype: {kind.mime}")
    return str(kind.extension), str(kind.mime)


def stripAudioFromVideo(video_filename, audio_filename):
    try:
        cmd = "ffmpeg -i " + video_filename + " -ac 1 -ar 44100 -vn " + audio_filename
        os.system(cmd)
    except Exception as err:
        logger.error(err.stderr)
        raise
    return True
