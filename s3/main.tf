resource "aws_s3_bucket" "incoming_audio" {
  bucket = var.whisper_incoming_audio_bucket

  tags = {
    Name        = var.whisper_incoming_audio_bucket
    Environment = var.environment
  }
}

resource "aws_s3_bucket" "outgoing_text" {
  bucket = var.whisper_outgoing_text_bucket

  tags = {
    Name        = var.whisper_outgoing_text_bucket
    Environment = var.environment
  }
}

resource "aws_s3_bucket_acl" "incoming_audio_acl" {
  bucket = aws_s3_bucket.incoming_audio.id
  acl    = "private"
}

resource "aws_s3_bucket_acl" "outgoing_text_acl" {
  bucket = aws_s3_bucket.outgoing_text.id
  acl    = "private"
}
