# Deploy OpsForge to AWS

Write-Host "🚀 Deploying OpsForge AI to AWS..." -ForegroundColor Cyan

# Check AWS CLI
if (!(Get-Command aws -ErrorAction SilentlyContinue)) {
    Write-Host "❌ AWS CLI not found" -ForegroundColor Red
    exit 1
}

# Package Lambda
Write-Host "`n📦 Packaging Lambda function..." -ForegroundColor Yellow
.\package_lambda.bat

if (!(Test-Path "opsforge-lambda.zip")) {
    Write-Host "❌ Package failed" -ForegroundColor Red
    exit 1
}

# Create S3 bucket for deployment
$bucketName = "opsforge-deployment-$(Get-Random)"
Write-Host "`n📦 Creating S3 bucket: $bucketName" -ForegroundColor Yellow
aws s3 mb s3://$bucketName --region us-east-1

# Deploy with SAM
Write-Host "`n🚀 Deploying to AWS..." -ForegroundColor Yellow
sam deploy `
    --template-file aws/template.yaml `
    --stack-name opsforge-ai `
    --s3-bucket $bucketName `
    --capabilities CAPABILITY_IAM `
    --region us-east-1 `
    --parameter-overrides AnthropicApiKey=$env:ANTHROPIC_API_KEY

Write-Host "`n✅ Deployment complete!" -ForegroundColor Green
Write-Host "`nGet API endpoint:" -ForegroundColor Cyan
Write-Host "aws cloudformation describe-stacks --stack-name opsforge-ai --query 'Stacks[0].Outputs'" -ForegroundColor Gray
