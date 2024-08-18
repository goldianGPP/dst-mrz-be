import threading
import boto3
import base64
from dst_mrz_parent.settings import S3
import logging
logger = logging.getLogger("dst-mrz-be")

class S3StorageService:
    _instance = None
    _lock = threading.Lock()

    def __new__(cls, *args, **kwargs):
        if not cls._instance:
            with cls._lock:
                cls._instance = super(S3StorageService, cls).__new__(cls, *args, **kwargs)
        return cls._instance

    def put_object(self, image, bucket_id, object_name):
        binary_data = base64.b64decode(image)
        s3 = boto3.client("s3")

        bucket_name = S3[bucket_id]['bucket_name']
        object_name = f"{S3[bucket_id]['suffix']}{object_name}"
        try:
            logger.info(f"saving {object_name} to s3 storage")
            response = s3.put_object(Body=binary_data, Bucket=bucket_name, Key=object_name)
            logger.info(f"File uploaded successfully. ETag: {response['ETag']}")
        except Exception as e:
            logger.error(f"Error uploading file to S3: {e}")
            raise e
