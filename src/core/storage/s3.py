import aioboto3
from botocore.exceptions import NoCredentialsError, ClientError
from typing import BinaryIO, Optional, List, Dict, Any
import io
from . import StorageBackend

class S3StorageBackend(StorageBackend):
    """S3-compatible storage backend (works with MinIO, AWS S3, etc.)"""
    
    def __init__(
        self,
        endpoint_url: str,
        access_key_id: str,
        secret_access_key: str,
        bucket_name: str,
        region: str = "us-east-1",
        secure: bool = True
    ):
        self.endpoint_url = endpoint_url
        self.access_key_id = access_key_id
        self.secret_access_key = secret_access_key
        self.bucket_name = bucket_name
        self.region = region
        self.secure = secure
        self._session = aioboto3.Session()
    
    def _get_client(self):
        """Get S3 client"""
        return self._session.client(
            's3',
            endpoint_url=self.endpoint_url,
            aws_access_key_id=self.access_key_id,
            aws_secret_access_key=self.secret_access_key,
            region_name=self.region,
            use_ssl=self.secure
        )
    
    async def upload(self, key: str, file: BinaryIO, metadata: Optional[Dict[str, str]] = None) -> str:
        """Upload a file to S3"""
        try:
            async with self._get_client() as s3:
                # Ensure we're at the beginning of the file
                file.seek(0)
                
                extra_args = {}
                if metadata:
                    extra_args['Metadata'] = metadata
                
                # Determine content type
                if key.endswith('.pdf'):
                    extra_args['ContentType'] = 'application/pdf'
                elif key.endswith('.json'):
                    extra_args['ContentType'] = 'application/json'
                elif key.endswith('.tex'):
                    extra_args['ContentType'] = 'text/x-tex'
                
                await s3.upload_fileobj(
                    file,
                    self.bucket_name,
                    key,
                    ExtraArgs=extra_args
                )
                
                return f"s3://{self.bucket_name}/{key}"
        except Exception as e:
            raise Exception(f"Failed to upload file: {str(e)}")
    
    async def download(self, key: str) -> BinaryIO:
        """Download a file from S3"""
        try:
            async with self._get_client() as s3:
                file_stream = io.BytesIO()
                await s3.download_fileobj(self.bucket_name, key, file_stream)
                file_stream.seek(0)
                return file_stream
        except ClientError as e:
            if e.response['Error']['Code'] == 'NoSuchKey':
                raise FileNotFoundError(f"File not found: {key}")
            raise Exception(f"Failed to download file: {str(e)}")
    
    async def delete(self, key: str) -> bool:
        """Delete a file from S3"""
        try:
            async with self._get_client() as s3:
                await s3.delete_object(Bucket=self.bucket_name, Key=key)
                return True
        except Exception as e:
            raise Exception(f"Failed to delete file: {str(e)}")
    
    async def exists(self, key: str) -> bool:
        """Check if a file exists in S3"""
        try:
            async with self._get_client() as s3:
                await s3.head_object(Bucket=self.bucket_name, Key=key)
                return True
        except ClientError as e:
            if e.response['Error']['Code'] == '404':
                return False
            raise
    
    async def list_files(self, prefix: str = "", limit: int = 100) -> List[Dict[str, Any]]:
        """List files in S3 with optional prefix"""
        try:
            async with self._get_client() as s3:
                response = await s3.list_objects_v2(
                    Bucket=self.bucket_name,
                    Prefix=prefix,
                    MaxKeys=limit
                )
                
                files = []
                for obj in response.get('Contents', []):
                    files.append({
                        'key': obj['Key'],
                        'size': obj['Size'],
                        'last_modified': obj['LastModified'],
                        'etag': obj['ETag']
                    })
                
                return files
        except Exception as e:
            raise Exception(f"Failed to list files: {str(e)}")
    
    async def get_presigned_url(self, key: str, expires_in: int = 3600) -> str:
        """Generate a presigned URL for temporary access"""
        try:
            async with self._get_client() as s3:
                url = await s3.generate_presigned_url(
                    'get_object',
                    Params={'Bucket': self.bucket_name, 'Key': key},
                    ExpiresIn=expires_in
                )
                return url
        except Exception as e:
            raise Exception(f"Failed to generate presigned URL: {str(e)}")
