resource "aws_iam_role" "lex_execution" {
  count = var.create_role ? 1 : 0
  name  = "${var.lexbot_role_name}-${var.environment}"

  assume_role_policy = jsonencode({
    Version = "2012-10-17",
    Statement = [{
      Effect = "Allow",
      Principal = {
        Service = "lexv2.amazonaws.com"
      },
      Action = "sts:AssumeRole"
    },
    {
      Effect: "Allow",
      Action: [
        "lex:StartImport",
        "lex:GetImport",
        "lex:ListImports",
        "lex:DescribeBot",
        "lex:ListBots",
        "lex:ListBotVersions",
        "lex:ListBotLocales",
        "lex:DescribeBotAlias",
        "lex:CreateBotAlias"
      ],
      Resource = "*"
    }]
  })
}

resource "aws_iam_role_policy_attachment" "lex_basic" {
  count = var.create_role ? 1 : 0
  role       = aws_iam_role.lex_execution[0].name
  policy_arn = "arn:aws:iam::aws:policy/AmazonLexFullAccess"
}
