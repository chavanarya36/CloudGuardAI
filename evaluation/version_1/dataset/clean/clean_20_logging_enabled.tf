resource "aws_flow_log" "vpc_flow" {
  vpc_id          = var.vpc_id
  traffic_type    = "ALL"
  log_destination = aws_cloudwatch_log_group.flow_logs.arn
  iam_role_arn    = var.flow_log_role_arn

  tags = {
    Name = "vpc-flow-log"
  }
}

resource "aws_cloudwatch_log_group" "flow_logs" {
  name              = "/vpc/flow-logs"
  retention_in_days = 90

  tags = {
    Environment = "production"
  }
}
