# Terraform template for AWS ECS/Fargate

This terraform setup can be used to setup the AWS infrastructure
for a dockerized application running on ECS with Fargate launch
configuration.

## Resources

This setup creates the following resources:

- VPC
- One public subnet
- Routing tables for the subnet
- Internet Gateway for public subnet
- Two security groups
  - one that allows HTTP/HTTPS access
  - one that allows access to the specified container port
- An ECR for the docker images
- An ECS cluster with a service (incl. auto scaling policies for CPU and memory usage)
  and task definition to run docker containers from the ECR (incl. IAM execution role)
- Secrets - a Terraform module that creates many secrets based on a `map` input value, and has a list of secret ARNs as an output value

![example](https://d2908q01vomqb2.cloudfront.net/1b6453892473a467d07372d45eb05abc2031647a/2018/01/26/Slide2-1024x866.png "Infrastructure illustration")
(Source: https://aws.amazon.com/de/blogs/compute/task-networking-in-aws-fargate/)

### Get Started building your own infrastructure

- Install terraform on MacOS with `brew install terraform`
- create your own `secrets.tfvars` based on `secrets.example.tfvars`, insert the values for your AWS access key and secrets. If you don't create your `secrets.tfvars`, don't worry. Terraform will interactively prompt you for missing variables later on. You can also create your `environment.tfvars` file to manage non-secret values for different environments or projects with the same infrastructure
- execute `terraform init`, it will initialize your local terraform and connect it to the state store, and it will download all the necessary providers
- execute `terraform plan -var-file="secrets.tfvars" -var-file="environment.tfvars" -out="out.plan"` - this will calculate the changes terraform has to apply and creates a plan. If there are changes, you will see them. Check if any of the changes are expected, especially deletion of infrastructure.
- if everything looks good, you can execute the changes with `terraform apply out.plan`

### Setting up Terraform Backend

Sometimes we need to setup the Terraform Backend from Scratch, if we need to setup a completely separate set of Infrastructure or start a new project. This involves setting up a backend where Terraform keeps track of the state outside your local machine, and hooking up Terraform with AWS.
Here is a guideline:

1. Setup AWS CLI on MacOS with `brew install aws-cli`
   1. Get access key and secret from IAM for your user
   1. execute `aws configure` .. enter your key and secret
   1. find your credentials stored in files within `~/.aws` folder
1. Create s3 bucket to hold our terraform state with this command: `aws s3api create-bucket --bucket my-terraform-backend-store --region us-west-2 --create-bucket-configuration LocationConstraint=us-west-2`
1. Because the terraform state contains some very secret secrets, setup encryption of bucket: `aws s3api put-bucket-encryption --bucket my-terraform-backend-store --server-side-encryption-configuration "{\"Rules\":[{\"ApplyServerSideEncryptionByDefault\":{\"SSEAlgorithm\":\"AES256\"}}]}"`
1. Create IAM user for Terraform `aws iam create-user --user-name my-terraform-user`
1. Add policy to access S3 and DynamoDB access -

   - `aws iam attach-user-policy --policy-arn arn:aws:iam::aws:policy/AmazonS3FullAccess --user-name my-terraform-user`
   - `aws iam attach-user-policy --policy-arn arn:aws:iam::aws:policy/AmazonDynamoDBFullAccess --user-name my-terraform-user`

1. Create bucket policy, put against bucket `aws s3api put-bucket-policy --bucket my-terraform-backend-store --policy file://policy.json`. Here is the policy file - the actual ARNs need to be adjusted based on the output of the steps above:

   ```sh
    cat <<-EOF >> policy.json
    {
        "Statement": [
            {
                "Effect": "Allow",
                "Principal": {
                    "AWS": "arn:aws:iam::937707138518:user/my-terraform-user"
                },
                "Action": "s3:*",
                "Resource": "arn:aws:s3:::my-terraform-backend-store"
            }
        ]
    }
    EOF
   ```

1. Enable versioning in bucket with `aws s3api put-bucket-versioning --bucket terraform-remote-store --versioning-configuration Status=Enabled`
1. create the AWS access keys for your deployment user with `aws iam create-access-key --user-name my-terraform-user`, this will output access key and secret, which can be used as credentials for executing Terraform against AWS - i.e. you can put the values into the `secrets.tfvars` file
1. execute initial terraforming
1. after initial terraforming, the state lock dynamo DB table is created and can be used for all subsequent executions. Therefore, this line in `main.tf` can be un-commented:

```hcl
    # dynamodb_table = "terraform-state-lock-dynamo" - uncomment this line once the terraform-state-lock-dynamo has been terraformed
```

### SSHing into running task container

Need to set `enable_execute_command = true` in ecs_service resource, and add policy changes specified below:
[https://aws.amazon.com/blogs/containers/new-using-amazon-ecs-exec-access-your-containers-fargate-ec2/](https://aws.amazon.com/blogs/containers/new-using-amazon-ecs-exec-access-your-containers-fargate-ec2/)

### Local testing of task container
docker compose up --build

### Notes
https://github.com/pyannote/pyannote-audio/pull/1098
https://colab.research.google.com/drive/12W6bR-C6NIEjAML19JubtzHPIlVxdaUq?usp=sharing
https://github.com/openai/whisper/discussions/264

lambda to fargate example
https://gist.github.com/fermayo/02b0f69cd942115f8c70e6802516f368
run_task doc
https://boto3.amazonaws.com/v1/documentation/api/latest/reference/services/ecs.html#ECS.Client.run_task
more run_task examples
https://hands-on.cloud/working-with-ecs-in-python-using-boto3/

`# aws ecs execute-command --region us-west-2 --cluster $NAME-cluster-dev --task fee34e07568e4592a6b1fc43e1ad657f --container $NAME-container-dev --command "/bin/bash" --interactive`