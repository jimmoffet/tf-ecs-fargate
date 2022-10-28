resource "aws_s3_bucket" "this" {
  bucket = var.whisper_incoming_audio_bucket

  tags = {
    Name        = var.whisper_incoming_audio_bucket
    Environment = var.environment
  }
}

resource "aws_s3_bucket_acl" "example" {
  bucket = aws_s3_bucket.this.id
  acl    = "private"
}
