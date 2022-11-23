import boto3
import os
import json

# application-secrets dict from secrets.tfvars will be injected by aws as env vars


def lambda_handler(event, context):
    try:
        postBody = json.loads(event["body"])
    except:
        postBody = event["body"]
    print(postBody)
    url = "no-url-sent"
    if "job_id" in postBody:
        url = postBody["url"]
    job_id = "xxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxx"
    if "job_id" in postBody:
        job_id = postBody["job_id"]

    s3_client = boto3.client("s3")
    output_bucket = os.getenv(
        "S3_OUTGOING_BUCKET",
        "whisper-outgoing-text-bucket",
    )

    try:
        file_content = (
            s3_client.get_object(Bucket=output_bucket, Key=f"dev/{job_id}.txt")["Body"]
            .read()
            .decode("utf-8")
        )
        print(file_content)
        response = {
            "statusCode": 200,
            "body": {"transcription": str(file_content.strip())},
        }
        print(
            f"Completed transcription found for job_id: {job_id} with response: {response}"
        )
        return str(response)
    except Exception as err:
        print(f"Error attempting to obtain existing transcription: {err}")
        pass

    client = boto3.client("ecs")

    response = client.describe_tasks(
        cluster="src-fargate-demo-cluster-dev",
        tasks=[
            job_id,
        ],
    )

    if not response["failures"]:
        print(f"In progress task found for task id {job_id}: {response}")
        status = response["tasks"][0]["lastStatus"]
        task_arn = response["tasks"][0]["taskArn"]
        task_id = task_arn.split("/")[-1]
        output = {
            "statusCode": 200,
            "body": {"task_id": task_id, "transcription": None, "lastStatus": status},
        }
        return output

    response = client.run_task(
        cluster=os.getenv(
            "CLUSTER_ARN",
            "you-forgot-to-set-cluster-arn-env-var",
        ),
        launchType="FARGATE",
        taskDefinition=os.getenv(
            "TASK_DEFINITION_ARN",
            "you-forgot-to-set-task-def-arn-env-var",
        ),
        count=int(os.getenv("COUNT", 1)),
        platformVersion="LATEST",
        overrides={
            "containerOverrides": [
                {
                    "name": os.getenv("NAME", "you-forgot-to-set-name-env-var")
                    + "-container-dev",
                    "command": [url],
                }
            ]
        },
        networkConfiguration={
            "awsvpcConfiguration": {
                "subnets": [
                    os.getenv("SUBNET_1", "you-forgot-to-set-subnet-1-arn-env-var"),
                    os.getenv("SUBNET_2", "you-forgot-to-set-subnet-2-arn-env-var"),
                ],
                "assignPublicIp": "ENABLED",
            },
        },
    )
    print(f"response: {response}")
    task_arn = response["tasks"][0]["taskArn"]
    print(f"task_arn: {task_arn}")
    task_id = task_arn.split("/")[-1]
    print(f"task_id: {task_id}")
    output = {
        "statusCode": 200,
        "body": {"task_id": task_id, "transcription": None, "lastStatus": "Pending"},
    }
    return output
