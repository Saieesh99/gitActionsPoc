resource "aws_iam_role" "lex_execution" {
  count = var.create_lambda_role ? 1 : 0
  name = var.lambda_role_name

  assume_role_policy = jsonencode({
    Version = "2012-10-17",
    Statement = [{
      Effect = "Allow",
      Principal = {
        Service = "lexv2.amazonaws.com"
      },
      Action = "sts:AssumeRole"
    }]
  })
}

resource "aws_iam_role_policy_attachment" "lex_basic" {
  count = var.create_lambda_role ? 1 : 0
  role       = aws_iam_role.lex_execution.name
  policy_arn = "arn:aws:iam::aws:policy/AmazonLexFullAccess"
}
