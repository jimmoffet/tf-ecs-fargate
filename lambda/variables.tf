variable "name" {
  description = "the name of your stack, e.g. \"demo\""
}

variable "layer_environment" {
  description = "a set of environment variables to pass to the lambda function"
}

variable "environment" {
  description = "the name of your environment, e.g. \"prod\""
}

variable "region" {
  description = "the AWS region in which resources are created"
}

variable "whisper_incoming_audio_bucket" {
  description = "The name of the S3 bucket where incoming audio files are stored"
}

variable "whisper_outgoing_text_bucket" {
  description = "The name of the S3 bucket where outgoing text files are stored"
}
