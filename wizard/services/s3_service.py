import os
import uuid
import boto3
from botocore.config import Config
from pathlib import Path
from dotenv import load_dotenv

# Load env from root
env_path = Path(__file__).resolve().parent.parent.parent / '.env'
load_dotenv(dotenv_path=env_path)

class S3Service:
    def __init__(self):
        self.access_key = os.getenv("S3_ACCESS_KEY")
        self.secret_key = os.getenv("S3_SECRET_KEY")
        self.account_id = os.getenv("CLOUDFLARE_ACCOUNT_ID")
        self.bucket = os.getenv("R2_BUCKET_NAME")
        self.base_url = os.getenv("R2_BASE_URL", "").rstrip("/")
        
        # Cloudflare R2 specific endpoint URL
        self.endpoint_url = f"https://{self.account_id}.r2.cloudflarestorage.com"
        
        if self.access_key and self.secret_key and self.account_id:
            self.s3 = boto3.client(
                's3',
                endpoint_url=self.endpoint_url,
                aws_access_key_id=self.access_key,
                aws_secret_access_key=self.secret_key,
                config=Config(signature_version='s3v4'),
                region_name=os.getenv("S3_REGION", "auto")
            )
        else:
            self.s3 = None

    def upload_file(self, file_obj, filename: str, content_type: str = None) -> str:
        """
        Uploads a file object to R2 and returns the public URL.
        """
        if not self.s3:
            raise ValueError("Cloudflare R2/S3 credentials not configured properly in .env")
            
        # Ensure a unique filename to prevent overwriting
        unique_filename = f"{uuid.uuid4().hex}_{filename}"
        
        extra_args = {}
        if content_type:
            extra_args['ContentType'] = content_type
            
        try:
            self.s3.upload_fileobj(
                file_obj, 
                self.bucket, 
                unique_filename,
                ExtraArgs=extra_args
            )
            
            # Return the public URL
            return f"{self.base_url}/{unique_filename}"
            
        except Exception as e:
            print(f"S3 Upload Error: {e}")
            raise Exception(f"Failed to upload to S3/R2: {e}")
