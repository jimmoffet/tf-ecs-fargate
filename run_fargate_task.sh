#!/bin/bash
#
# Runs an AWS Fargate task
#
# Dependencies:
#
# - aws
# - jq
#
# Usage:
#
# $ ./run_fargate_task.sh TASK_NAME [TASK_ARGUMENT]
#

set -euo pipefail

NAME="$1"
URL="$2"
JOB_ID="$3"

echo $URL
echo $JOB_ID

# To pass an argument to the task
# Note: the "command" override acts to append arguments to the Dockerfile ENTRYPOINT
if [[ -z "$URL" ]]; then
  command_override="[]"
else
  command_override="[\"$URL\", \"$JOB_ID\"]"
fi
overrides='{
  "containerOverrides": [{
    "name": "'"$NAME-container-dev"'",
    "command": '"$command_override"'
  }]
}'

echo $command_override
echo $overrides

# Fetch configuration from the service, in order to run-task with same configuration
describe_service_response="$(aws ecs describe-services \
  --cluster "$NAME-cluster-dev" \
  --services "$NAME-service-dev"
)"
cluster_arn="$(echo "$describe_service_response" | jq -r .services[].clusterArn)"
launch_type="$(echo "$describe_service_response" | jq -r .services[].launchType)"
task_def_arn="$(echo "$describe_service_response" | jq -r .services[].taskDefinition)"
network_configuration="$(echo "$describe_service_response" | jq .services[].networkConfiguration)"

# Run the task with same configuration defined on the service, but with exception of "command" 
# override
run_task_response="$(aws ecs run-task \
  --cluster "$cluster_arn" \
  --task-definition "$task_def_arn" \
  --launch-type "$launch_type" \
  --overrides "$overrides" \
  --network-configuration "$network_configuration"
)"
task_arn="$(echo "$run_task_response" | jq -r .tasks[].taskArn)"

# Poll the task status until it stops
task_status=""
while [[ "$task_status" != "STOPPED" ]]; do
  sleep 3
  describe_task_response="$(aws ecs describe-tasks \
    --cluster "$cluster_arn" \
    --tasks "$task_arn")"
  new_task_status="$(echo "$describe_task_response" | jq -r .tasks[].lastStatus)"
  stopped_reason="$(echo "$describe_task_response" | jq -r .tasks[].stoppedReason)"

  # Print any changes in status
  if [[ "$new_task_status" != "$task_status" ]]; then
    task_status="$new_task_status"
    echo ""
    echo "Task status: $task_status"
    if [[ "$stopped_reason" != "null" ]]; then
      echo "Reason: $stopped_reason"
    fi
  fi

  printf .
done

# Display logs from the task
echo ""
echo "Task logs:"
task_id="$(echo "$task_arn" | cut -d/ -f3)"
echo "Task ARN: $task_arn"
echo "Task ID: $task_id"
# Use --start to workaround missing streams issue
awslogs get --start 12h --no-group --no-stream /ecs/$NAME-task-dev ecs/$NAME-container-dev/"$task_id"
