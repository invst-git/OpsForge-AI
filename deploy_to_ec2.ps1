# Deploy to EC2
# Usage: .\deploy_to_ec2.ps1 -KeyPath "path/to/key.pem" -EC2Host "ec2-xx-xx-xx-xx.compute.amazonaws.com"

param(
    [Parameter(Mandatory=$true)]
    [string]$KeyPath,

    [Parameter(Mandatory=$true)]
    [string]$EC2Host
)

Write-Host "Deploying to EC2: $EC2Host" -ForegroundColor Cyan

# Create temp directory for deployment
$tempDir = "opsforge-deploy-temp"
if (Test-Path $tempDir) { Remove-Item -Recurse -Force $tempDir }
New-Item -ItemType Directory -Path $tempDir | Out-Null

Write-Host "Copying files..." -ForegroundColor Yellow
# Copy only necessary files
Copy-Item -Recurse agents "$tempDir/"
Copy-Item -Recurse config "$tempDir/"
Copy-Item -Recurse data "$tempDir/"
Copy-Item -Recurse tools "$tempDir/"
Copy-Item -Recurse frontend "$tempDir/"
Copy-Item backend_api.py "$tempDir/"
Copy-Item live_data_generator.py "$tempDir/"
Copy-Item requirements.txt "$tempDir/"
Copy-Item ec2_setup.sh "$tempDir/"

# Upload to EC2
Write-Host "Uploading to EC2..." -ForegroundColor Yellow
scp -i $KeyPath -r "$tempDir/*" "ubuntu@${EC2Host}:/tmp/opsforge/"

# Run setup script
Write-Host "Running setup on EC2..." -ForegroundColor Yellow
ssh -i $KeyPath "ubuntu@$EC2Host" @"
sudo mkdir -p /opt/opsforge
sudo cp -r /tmp/opsforge/* /opt/opsforge/
sudo chown -R ubuntu:ubuntu /opt/opsforge
cd /opt/opsforge
chmod +x ec2_setup.sh
sudo ./ec2_setup.sh
"@

# Cleanup
Remove-Item -Recurse -Force $tempDir

Write-Host "Deployment complete!" -ForegroundColor Green
Write-Host "Access at: http://$EC2Host" -ForegroundColor Cyan
