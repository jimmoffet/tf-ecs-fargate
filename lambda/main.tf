data "aws_caller_identity" "current" {}

resource "aws_iam_role" "lambda_role" {
  name               = "${var.name}_Lambda_Function_Role"
  assume_role_policy = <<EOF
{
 "Version": "2012-10-17",
 "Statement": [
   {
     "Action": "sts:AssumeRole",
     "Principal": {
       "Service": "lambda.amazonaws.com"
     },
     "Effect": "Allow",
     "Sid": ""
   }
 ]
}
EOF
}

resource "aws_iam_policy" "iam_policy_for_lambda" {

  name        = "aws_iam_policy_for_terraform_aws_lambda_role"
  path        = "/"
  description = "AWS IAM Policy for managing aws lambda role"
  policy      = <<EOF
{
	"Version": "2012-10-17",
	"Statement": [{
			"Action": [
				"logs:CreateLogGroup",
				"logs:CreateLogStream",
				"logs:PutLogEvents"
			],
			"Resource": "arn:aws:logs:*:*:*",
			"Effect": "Allow"
		},
		{
			"Action": [
				"ecs:RunTask",
        "ecs:DescribeTasks"
			],
			"Resource": [
        "arn:aws:ecs:${var.region}:${data.aws_caller_identity.current.account_id}:task-definition/${var.name}-task-${var.environment}:*",
        "arn:aws:ecs:${var.region}:${data.aws_caller_identity.current.account_id}:task/${var.name}-cluster-${var.environment}/*"
      ],
			"Effect": "Allow"
		},
		{
			"Effect": "Allow",
			"Action": [
				"iam:PassRole"
			],
			"Resource": [
				"arn:aws:iam::${data.aws_caller_identity.current.account_id}:role/${var.name}-ecsTaskExecutionRole",
				"arn:aws:iam::${data.aws_caller_identity.current.account_id}:role/${var.name}-ecsTaskRole"
			]
		},
		{
			"Effect": "Allow",
			"Action": [
				"s3:DeleteObject",
				"s3:ListBucket",
				"s3:HeadObject",
				"s3:GetObject",
				"s3:GetObjectVersion",
				"s3:PutObject"
			],
			"Resource": [
				"arn:aws:s3:::${var.whisper_incoming_audio_bucket}/*",
				"arn:aws:s3:::${var.whisper_outgoing_text_bucket}/*"
			]
		}
	]
}
EOF
}

resource "aws_iam_role_policy_attachment" "attach_iam_policy_to_iam_role" {
  role       = aws_iam_role.lambda_role.name
  policy_arn = aws_iam_policy.iam_policy_for_lambda.arn
}

data "archive_file" "zip_the_python_code" {
  type             = "zip"
  source_dir       = "${path.module}/src/"
  output_file_mode = "0666"
  output_path      = "${path.module}/src/${var.name}-lambda-layer.zip"
}

resource "aws_lambda_function" "terraform_lambda_func" {
  filename         = "${path.module}/src/${var.name}-lambda-layer.zip"
  function_name    = "${var.name}_lambda_function_${var.environment}"
  role             = aws_iam_role.lambda_role.arn
  handler          = "index.lambda_handler"
  runtime          = "python3.9"
  source_code_hash = data.archive_file.zip_the_python_code.output_base64sha256
  depends_on       = [aws_iam_role_policy_attachment.attach_iam_policy_to_iam_role]
  environment {
    variables = var.layer_environment
  }
}


