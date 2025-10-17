
@echo off
echo Creating Lambda deployment package...

:: Create temp directory
if exist lambda_package rmdir /s /q lambda_package
mkdir lambda_package

:: Copy code
xcopy /E /I agents lambda_package\agents
xcopy /E /I tools lambda_package\tools
xcopy /E /I data lambda_package\data
copy aws\lambda_handler.py lambda_package\
copy .env lambda_package\

:: Install dependencies
pip install --target lambda_package strands-agents strands-agents-tools boto3 anthropic pydantic networkx

:: Create ZIP
cd lambda_package
powershell Compress-Archive -Path * -DestinationPath ..\opsforge-lambda.zip -Force
cd ..

echo Package created: opsforge-lambda.zip
