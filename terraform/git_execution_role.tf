resource "aws_iam_role" "lex_deploy_role" {
  name = "lex-deploy-role-${var.environment}"

  assume_role_policy = jsonencode({
    Version = "2012-10-17",
    Statement = [
      {
        Effect = "Allow",
        Principal = {
          AWS = "arn:aws:iam::${var.aws_account_id}:user/user5"
        },
        Action = "sts:AssumeRole"
      }
    ]
  })
}

resource "aws_iam_policy" "lex_admin_policy" {
  name = "LexBotFullPermissions-${var.environment}"

  policy = jsonencode({
    Version = "2012-10-17",
    Statement: [
      {
        Effect = "Allow",
        Action = [
          "lex:CreateBot",
          "lex:UpdateBot",
          "lex:DeleteBot",
          "lex:DescribeBot",
          "lex:ListBots",
          "lex:ListBotVersions",
          "lex:CreateBotLocale",
          "lex:DescribeBotLocale",
          "lex:BuildBotLocale",
          "lex:ListBotLocales",
          "lex:CreateIntent",
          "lex:ListIntents",
          "lex:StartImport",
          "lex:GetImport",
          "lex:ListImports",
          "lex:CreateBotAlias",
          "lex:UpdateBotAlias",
          "lex:ListBotAliases",
          "lex:TagResource",
          "lex:UntagResource"
        ],
        Resource = "*"
      }
    ]
  })
}

resource "aws_iam_role_policy_attachment" "attach_lex_policy" {
  role       = aws_iam_role.lex_deploy_role.name
  policy_arn = aws_iam_policy.lex_admin_policy.arn
}