import logging
import time
import random
from typing import Dict, Any, Optional

try:
    import boto3
    import botocore
    from botocore.exceptions import ClientError, BotoCoreError
except ImportError:
    boto3 = None
    botocore = None
    ClientError = Exception
    BotoCoreError = Exception

from src.models import IAMData
from src.iam_parser import IAMParser

logger = logging.getLogger(__name__)

class AWSExporter:
    def __init__(self, max_retries: int = 5, base_delay: float = 1.0, max_delay: float = 30.0):
        self.max_retries = max_retries
        self.base_delay = base_delay
        self.max_delay = max_delay
        
        if boto3 is None:
            raise ImportError("boto3 and botocore are required for AWS live export")
            
        self.client = boto3.client('iam')
        self.parser = IAMParser()

    def _call_with_backoff(self, operation, **kwargs) -> Dict[str, Any]:
        """Call a boto3 operation with exponential backoff and jitter."""
        retries = 0
        while True:
            try:
                return operation(**kwargs)
            except ClientError as e:
                error_code = e.response.get("Error", {}).get("Code", "")
                
                # Handle Rate Limit / Throttling
                if error_code in ["Throttling", "ThrottlingException", "RequestLimitExceeded", "RateExceeded"]:
                    if retries >= self.max_retries:
                        logger.error(f"Max retries reached for {operation.__name__}")
                        raise
                        
                    # Calculate delay with exponential backoff and jitter
                    delay = min(self.max_delay, self.base_delay * (2 ** retries))
                    jitter = random.uniform(0, delay * 0.1)
                    sleep_time = delay + jitter
                    
                    logger.warning(f"Rate limited on {operation.__name__}. Retrying in {sleep_time:.2f}s...")
                    time.sleep(sleep_time)
                    retries += 1
                else:
                    raise
            except (BotoCoreError, Exception) as e:
                raise

    def export_iam_data(self) -> IAMData:
        """Export all IAM data using get_account_authorization_details and parse it."""
        logger.info("Starting live IAM export...")
        
        raw_data: Dict[str, Any] = {
            "UserDetailList": [],
            "GroupDetailList": [],
            "RoleDetailList": [],
            "Policies": []
        }
        
        try:
            paginator = self.client.get_paginator('get_account_authorization_details')
            # Paginators don't retry automatically for Throttling in some older botocore versions,
            # but we can apply backoff manually on paginate() iteration if needed, though botocore usually retries internally.
            # To be safe, we wrap the whole page generator if we want, but typically botocore handles pagination retries.
            for page in paginator.paginate():
                for key in ["UserDetailList", "GroupDetailList", "RoleDetailList", "Policies"]:
                    if key in page:
                        raw_data[key].extend(page[key])
        except ClientError as e:
            error_code = e.response.get("Error", {}).get("Code", "")
            if error_code == "AccessDenied":
                logger.warning("Access denied when calling get_account_authorization_details. Returning partial or empty data.")
            else:
                logger.error(f"Failed to export IAM data: {e}")
                raise
        except Exception as e:
            logger.error(f"Unexpected error during IAM export: {e}")
            raise
            
        # Get account ID if possible
        account_id = "000000000000"
        try:
            sts = boto3.client('sts')
            account_id = self._call_with_backoff(sts.get_caller_identity).get("Account", account_id)
        except Exception as e:
            logger.warning(f"Could not retrieve AWS Account ID: {e}")
            
        iam_data = self.parser.parse(raw_data)
        iam_data.account_id = account_id
        
        return iam_data
