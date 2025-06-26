"""
AWS S3-specific storage backend
"""

from .base import StorageBackend, BackendConfig, BackendCapability
import aioboto3
from typing import BinaryIO, Optional, List, Dict, Any
import io


class AWSS3Backend(StorageBackend):
    """AWS S3 storage backend with AWS-specific features"""
    
    @classmethod
    def create_config(
        cls,
        name: str,
        access_key: str,
        secret_key: str,
        bucket_name: str,
        region: str,
        storage_class: str = "STANDARD"
    ) -> BackendConfig:
        """Create an AWS S3 backend configuration"""
        return BackendConfig(
            name=name,
            backend_type="aws_s3",
            capabilities=[
                BackendCapability.VERSIONING,
                BackendCapability.ENCRYPTION,
                BackendCapability.LIFECYCLE_RULES,
                BackendCapability.TAGGING,
                BackendCapability.REPLICATION,
                BackendCapability.SIGNED_URLS,
                BackendCapability.MULTIPART_UPLOAD,
                BackendCapability.SERVER_SIDE_COPY,
            ],
            config={
                "access_key": access_key,
                "secret_key": secret_key,
                "bucket_name": bucket_name,
                "region": region,
                "storage_class": storage_class
            }
        )
    
    def _validate_config(self) -> None:
        """Validate AWS S3 configuration"""
        required = ["access_key", "secret_key", "bucket_name", "region"]
        for field in required:
            if field not in self.config.config:
                raise ValueError(f"Missing required config field: {field}")
    
    def _initialize(self) -> None:
        """Initialize AWS S3 connection"""
        self._session = aioboto3.Session()
        self._bucket_name = self.config.config["bucket_name"]
        self._storage_class = self.config.config.get("storage_class", "STANDARD")
    
    def _get_client(self):
        """Get AWS S3 client"""
        return self._session.client(
            's3',
            aws_access_key_id=self.config.config["access_key"],
            aws_secret_access_key=self.config.config["secret_key"],
            region_name=self.config.config["region"]
        )
    
    async def upload(self, key: str, file: BinaryIO, metadata: Optional[Dict[str, str]] = None) -> Dict[str, Any]:
        """Upload to AWS S3 with AWS-specific features"""
        try:
            async with self._get_client() as s3:
                file.seek(0)
                
                # AWS-specific upload arguments
                extra_args = {
                    'Metadata': metadata or {},
                    'StorageClass': self._storage_class,
                    'ServerSideEncryption': 'AES256'  # AWS-specific
                }
                
                # Add intelligent tiering if specified
                if self._storage_class == "INTELLIGENT_TIERING":
                    extra_args['StorageClass'] = 'INTELLIGENT_TIERING'
                
                # Upload
                await s3.upload_fileobj(
                    file,
                    self._bucket_name,
                    key,
                    ExtraArgs=extra_args
                )
                
                # Get object info
                head_response = await s3.head_object(
                    Bucket=self._bucket_name,
                    Key=key
                )
                
                return {
                    "key": key,
                    "etag": head_response['ETag'],
                    "size": head_response['ContentLength'],
                    "storage_class": head_response.get('StorageClass'),
                    "encryption": head_response.get('ServerSideEncryption'),
                    "version_id": head_response.get('VersionId'),
                    "backend": self.name
                }
        
        except Exception as e:
            raise Exception(f"AWS S3 upload failed: {str(e)}")
    
    # AWS-specific methods
    
    async def transition_to_glacier(self, key: str) -> bool:
        """Transition object to Glacier storage class"""
        try:
            async with self._get_client() as s3:
                # Copy object with new storage class
                copy_source = {'Bucket': self._bucket_name, 'Key': key}
                await s3.copy_object(
                    CopySource=copy_source,
                    Bucket=self._bucket_name,
                    Key=key,
                    StorageClass='GLACIER'
                )
                return True
        except Exception as e:
            raise Exception(f"Failed to transition to Glacier: {str(e)}")
    
    async def restore_from_glacier(self, key: str, days: int = 1) -> bool:
        """Restore object from Glacier"""
        try:
            async with self._get_client() as s3:
                await s3.restore_object(
                    Bucket=self._bucket_name,
                    Key=key,
                    RestoreRequest={
                        'Days': days,
                        'GlacierJobParameters': {
                            'Tier': 'Expedited'  # or 'Standard' or 'Bulk'
                        }
                    }
                )
                return True
        except Exception as e:
            raise Exception(f"Failed to restore from Glacier: {str(e)}")
