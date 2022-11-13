# Adapted from https://gist.github.com/fermayo/02b0f69cd942115f8c70e6802516f368

import os
import json
import boto3
from botocore.exceptions import ClientError


def get_transcription(bucket, job_id):
    s3 = boto3.resource("s3")
    try:
        s3.Bucket(bucket).download_file("dev/" + job_id + ".txt", "data.txt")
        with open("data.txt", "r") as file:
            string_data = file.read()
        file.close()
        return string_data
    except ClientError as e:
        if e.response["Error"]["Code"] == "404":
            return False
        else:
            raise


def lambda_handler(event, context):
    client = boto3.client("ecs")
    bucket = "whisper-outgoing-text-bucket"

    # TODO: get these from the event
    audio_url = "https://github.com/AssemblyAI-Examples/audio-intelligence-dashboard/raw/master/gettysburg10.wav"
    job_id = "fake_job_id_from_local_test_lambda"

    if job_id:
        transcription = get_transcription(bucket, job_id)
        if transcription:
            return {"statusCode": 200, "body": {"transcription": transcription}}

    describe_services_response = client.describe_services(
        cluster="src-fargate-demo-cluster-dev",
        services=[
            "src-fargate-demo-service-dev",
        ],
    )
    cluster_arn = describe_services_response["services"][0]["clusterArn"]
    task_def_arn = describe_services_response["services"][0]["taskDefinition"]
    network_configuration = describe_services_response["services"][0][
        "networkConfiguration"
    ]
    os.environ["CLUSTER"] = cluster_arn
    os.environ["TASK_DEFINITION"] = task_def_arn
    os.environ["NETWORK_CONFIGURATION"] = json.dumps(network_configuration)
    # os.environ["SUBNETS"] = "foo" # can be obtained from network configuration of the service
    print(f'os.environ["CLUSTER"]: {os.environ["CLUSTER"]}')
    print(f'os.environ["TASK_DEFINITION"]: {os.environ["TASK_DEFINITION"]}')
    print(f'os.environ["NETWORK_CONFIGURATION"]: {os.environ["NETWORK_CONFIGURATION"]}')

    response = client.run_task(
        cluster=os.getenv("CLUSTER"),
        launchType="FARGATE",
        taskDefinition=os.getenv("TASK_DEFINITION"),
        platformVersion="LATEST",
        networkConfiguration=json.loads(os.getenv("NETWORK_CONFIGURATION")),
        overrides={
            "containerOverrides": [
                {
                    "name": "src-fargate-demo-container-dev",
                    "command": [
                        audio_url,
                        job_id,
                    ],
                    # "environment": [
                    #     {
                    #         "name": "string",
                    #         "value": "string"
                    #     },
                    # ],
                    # "cpu": 123,
                    # "memory": 123,
                    # "memoryReservation": 123,
                    # "resourceRequirements": [
                    #     {
                    #         "value": "string",
                    #         "type": "GPU"|"InferenceAccelerator"
                    #     },
                    # ]
                },
            ],
            # "cpu": "string",
            # "inferenceAcceleratorOverrides": [
            #     {
            #         "deviceName": "string",
            #         "deviceType": "string"
            #     },
            # ],
            # "ephemeralStorage": {
            #     "sizeInGiB": 123
            # }
        },
    )
    print(f"response: {response}")

    task_arn = describe_services_response["tasks"][0]["taskArn"]
    print(f"task_arn: {task_arn}")

    return {"statusCode": 200, "body": {"job_id": job_id}}


response = lambda_handler(None, None)
print(f"response: {response}")
