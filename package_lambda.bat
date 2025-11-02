@echo off
echo Creating Lambda deployment package...

:: Create temp directory
if exist lambda_package rmdir /s /q lambda_package
mkdir lambda_package

:: Copy code
xcopy /E /I agents lambda_package\agents
xcopy /E /I config lambda_package\config
xcopy /E /I data lambda_package\data
copy aws\lambda_handler.py lambda_package\

:: Install dependencies (no anthropic, no strands)
pip install --target lambda_package boto3 pydantic networkx fastapi python-dotenv

:: Create ZIP
cd lambda_package
powershell Compress-Archive -Path * -DestinationPath ..\opsforge-lambda.zip -Force
cd ..

echo Package created: opsforge-lambda.zip
echo.
echo Size:
powershell Get-Item opsforge-lambda.zip ^| Select-Object Name, @{Name="SizeMB";Expression={[Math]::Round($_.Length / 1MB, 2)}}
