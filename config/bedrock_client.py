"""AWS Bedrock client wrapper that mimics Anthropic API interface"""

import boto3
import json
import os
import time
import random
from typing import List, Dict, Optional
from threading import Semaphore
from botocore.exceptions import ClientError


class BedrockClient:
    """Wrapper for AWS Bedrock that provides Anthropic-like API with rate limiting"""

    # Class-level semaphore to limit concurrent requests across all instances
    _semaphore = Semaphore(int(os.getenv('BEDROCK_MAX_CONCURRENT_REQUESTS', '3')))

    def __init__(self, region_name: str = None):
        self.region_name = region_name or os.getenv('AWS_REGION', 'us-east-1')
        self.bedrock_runtime = boto3.client(
            service_name='bedrock-runtime',
            region_name=self.region_name
        )
        self.max_retries = int(os.getenv('BEDROCK_MAX_RETRIES', '5'))

    class Messages:
        """Messages API compatible with Anthropic SDK"""

        def __init__(self, bedrock_runtime, region_name, max_retries, semaphore):
            self.bedrock_runtime = bedrock_runtime
            self.region_name = region_name
            self.max_retries = max_retries
            self.semaphore = semaphore

        def create(
            self,
            model: str,
            max_tokens: int,
            system: str,
            messages: List[Dict[str, str]],
            temperature: float = 1.0,
            top_p: float = 0.999
        ):
            """Create a message using Bedrock API with rate limiting and retry logic

            Args:
                model: Model ID (e.g., 'claude-sonnet-4-20250514')
                max_tokens: Maximum tokens to generate
                system: System prompt
                messages: List of message dicts with 'role' and 'content'
                temperature: Temperature for sampling
                top_p: Top-p for sampling

            Returns:
                Response object with .content[0].text attribute
            """
            # Convert short model name to full Bedrock model ID if needed
            if not model.startswith('us.') and not model.startswith('anthropic.'):
                # Map common model names to Bedrock IDs
                model_map = {
                    'claude-sonnet-4-20250514': 'us.anthropic.claude-sonnet-4-20250514-v1:0',
                    'claude-3-5-sonnet-20241022': 'us.anthropic.claude-3-5-sonnet-20241022-v2:0',
                }
                model = model_map.get(model, f'us.anthropic.{model}-v1:0')

            # Build Bedrock request body
            request_body = {
                "anthropic_version": "bedrock-2023-05-31",
                "max_tokens": max_tokens,
                "system": system,
                "messages": messages,
                "temperature": temperature,
                "top_p": top_p
            }

            # Retry logic with exponential backoff and semaphore-based rate limiting
            last_exception = None
            for attempt in range(self.max_retries):
                try:
                    # Acquire semaphore to limit concurrent requests
                    with self.semaphore:
                        # Call Bedrock
                        response = self.bedrock_runtime.invoke_model(
                            modelId=model,
                            body=json.dumps(request_body)
                        )

                        # Parse response
                        response_body = json.loads(response['body'].read())

                        # Create response object that mimics Anthropic API
                        return BedrockResponse(response_body)

                except ClientError as e:
                    error_code = e.response.get('Error', {}).get('Code', '')
                    last_exception = e

                    # Only retry on throttling errors
                    if error_code == 'ThrottlingException':
                        if attempt < self.max_retries - 1:
                            # Exponential backoff with jitter: 2^attempt * (1 + random 0-0.5)
                            base_delay = 2 ** attempt
                            jitter = random.uniform(0, 0.5)
                            wait_time = base_delay * (1 + jitter)

                            time.sleep(wait_time)
                            continue
                    # For other errors, don't retry
                    raise

            # If all retries exhausted, raise the last exception
            raise last_exception

    @property
    def messages(self):
        """Return Messages API instance"""
        return self.Messages(
            self.bedrock_runtime,
            self.region_name,
            self.max_retries,
            self._semaphore
        )


class BedrockResponse:
    """Response object that mimics Anthropic API response"""

    def __init__(self, response_body: Dict):
        self.response_body = response_body
        self._content = None

    @property
    def content(self):
        """Return content list mimicking Anthropic API"""
        if self._content is None:
            content_blocks = self.response_body.get('content', [])
            self._content = [BedrockContentBlock(block) for block in content_blocks]
        return self._content


class BedrockContentBlock:
    """Content block that mimics Anthropic API content block"""

    def __init__(self, block: Dict):
        self.block = block

    @property
    def text(self):
        """Return text content"""
        return self.block.get('text', '')

    @property
    def type(self):
        """Return block type"""
        return self.block.get('type', 'text')
