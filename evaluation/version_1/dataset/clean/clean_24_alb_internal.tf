resource "aws_lb" "internal" {
  name               = "internal-alb"
  internal           = true
  load_balancer_type = "application"
  security_groups    = [var.alb_sg_id]
  subnets            = var.private_subnet_ids

  enable_deletion_protection = true

  access_logs {
    bucket  = var.alb_logs_bucket
    prefix  = "internal-alb"
    enabled = true
  }

  tags = {
    Name        = "internal-alb"
    Environment = "production"
  }
}
