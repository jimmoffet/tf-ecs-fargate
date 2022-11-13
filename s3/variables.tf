variable "acl_value" {
  description = "The canned ACL to apply"
  default     = "private"
}

variable "whisper_incoming_audio_bucket" {
  description = "The name of the S3 bucket where incoming audio files are stored"
}

variable "whisper_outgoing_text_bucket" {
  description = "The name of the S3 bucket where outgoing text files are stored"
}

variable "environment" {
  description = "the name of your environment, e.g. \"prod\""
}
