"""
MinIO-specific storage backend
"""

import aioboto3
from botocore.exceptions import ClientError
from typing import BinaryIO, Optional, List, Dict, Any
import io
from datetime import datetime

from .base import StorageBackend, BackendConfig, BackendCapability, FileMetadata


class MinIOBackend(StorageBackend):
    """MinIO storage backend with full S3 compatibility"""
    
    @classmethod
    def create_config(
        cls,
        name: str,
        endpoint_url: str,
        access_key: str,
        secret_key: str,
        bucket_name: str,
        secure: bool = True,
        region: str = "us-east-1"
    ) -> BackendConfig:
        """Create a MinIO backend configuration"""
        return BackendConfig(
            name=name,
            backend_type="minio",
            capabilities=[
                BackendCapability.VERSIONING,
                BackendCapability.METADATA,
                BackendCapability.TAGGING,
                BackendCapability.PRESIGNED_URLS,
                BackendCapability.COMPRESSION,
                BackendCapability.LIFECYCLE_MANAGEMENT,
            ],
            config={
                "endpoint_url": endpoint_url,
                "access_key": access_key,
                "secret_key": secret_key,
                "bucket_name": bucket_name,
                "secure": secure,
                "region": region
            }
        )
    
    async def initialize(self) -> bool:
        """Initialize MinIO connection"""
        try:
            # Validate configuration
            required = ["endpoint_url", "access_key", "secret_key", "bucket_name"]
            for field in required:
                if field not in self.config.config:
                    raise ValueError(f"Missing required config field: {field}")
            
            self._session = aioboto3.Session()
            self._endpoint_url = self.config.config["endpoint_url"]
            self._bucket_name = self.config.config["bucket_name"]
            
            # MinIO-specific initialization
            self._use_path_style = True  # MinIO requires path-style access
            
            # Test connection by trying to head the bucket
            async with self._get_client() as s3:
                try:
                    await s3.head_bucket(Bucket=self._bucket_name)
                except ClientError as e:
                    if e.response['Error']['Code'] == '404':
                        # Bucket doesn't exist, try to create it
                        await s3.create_bucket(Bucket=self._bucket_name)
                    else:
                        raise
            
            self._initialized = True
            return True
        except Exception:
            return False
    
    async def health_check(self) -> bool:
        """Check if MinIO backend is healthy"""
        try:
            async with self._get_client() as s3:
                await s3.head_bucket(Bucket=self._bucket_name)
                return True
        except Exception:
            return False
    
    def _get_client(self):
        """Get MinIO S3 client"""
        return self._session.client(
            's3',
            endpoint_url=self._endpoint_url,
            aws_access_key_id=self.config.config["access_key"],
            aws_secret_access_key=self.config.config["secret_key"],
            region_name=self.config.config.get("region", "us-east-1"),
            use_ssl=self.config.config.get("secure", True),
            config=aioboto3.session.Config(
                s3={'addressing_style': 'path'}  # MinIO preference
            )
        )
    
    async def save(self, key: str, file: BinaryIO, metadata: Optional[Dict[str, str]] = None) -> Dict[str, Any]:
        """Upload to MinIO with MinIO-specific features"""
        try:
            async with self._get_client() as s3:
                file.seek(0)
                
                # Prepare upload arguments
                extra_args = {
                    'Metadata': metadata or {},
                    'StorageClass': 'STANDARD'  # MinIO supports STANDARD and REDUCED_REDUNDANCY
                }
                
                # Add content type
                if key.endswith('.pdf'):
                    extra_args['ContentType'] = 'application/pdf'
                elif key.endswith('.json'):
                    extra_args['ContentType'] = 'application/json'
                
                # Add tags if provided in metadata
                if 'tags' in (metadata or {}):
                    extra_args['Tagging'] = metadata.pop('tags')
                
                # Upload
                response = await s3.upload_fileobj(
                    file,
                    self._bucket_name,
                    key,
                    ExtraArgs=extra_args
                )
                
                # Get object info for response
                head_response = await s3.head_object(
                    Bucket=self._bucket_name,
                    Key=key
                )
                
                return {
                    "key": key,
                    "etag": head_response['ETag'],
                    "size": head_response['ContentLength'],
                    "storage_class": head_response.get('StorageClass', 'STANDARD'),
                    "version_id": head_response.get('VersionId'),
                    "backend": self.name
                }
        
        except Exception as e:
            raise Exception(f"MinIO upload failed: {str(e)}")
    
    async def retrieve(self, key: str) -> BinaryIO:
        """Download from MinIO"""
        try:
            async with self._get_client() as s3:
                response = await s3.get_object(
                    Bucket=self._bucket_name,
                    Key=key
                )
                
                # Read the streaming body
                data = await response['Body'].read()
                return io.BytesIO(data)
        
        except ClientError as e:
            if e.response['Error']['Code'] == 'NoSuchKey':
                raise FileNotFoundError(f"File not found in MinIO: {key}")
            raise Exception(f"MinIO download failed: {str(e)}")
    
    async def delete(self, key: str) -> bool:
        """Delete object from MinIO"""
        try:
            async with self._get_client() as s3:
                await s3.delete_object(
                    Bucket=self._bucket_name,
                    Key=key
                )
                return True
        except Exception:
            return False
    
    async def exists(self, key: str) -> bool:
        """Check if object exists in MinIO"""
        try:
            async with self._get_client() as s3:
                await s3.head_object(
                    Bucket=self._bucket_name,
                    Key=key
                )
                return True
        except ClientError as e:
            if e.response['Error']['Code'] in ['404', 'NoSuchKey']:
                return False
            raise
        except Exception:
            return False
    
    async def get_metadata(self, key: str) -> Optional[FileMetadata]:
        """Get MinIO object metadata"""
        try:
            async with self._get_client() as s3:
                response = await s3.head_object(
                    Bucket=self._bucket_name,
                    Key=key
                )
                
                # Get tags separately if they exist
                tags = {}
                try:
                    tag_response = await s3.get_object_tagging(
                        Bucket=self._bucket_name,
                        Key=key
                    )
                    tags = {tag['Key']: tag['Value'] for tag in tag_response.get('TagSet', [])}
                except:
                    pass
                
                # Combine metadata and tags
                custom_metadata = response.get('Metadata', {}).copy()
                custom_metadata.update(tags)
                
                return FileMetadata(
                    key=key,
                    size=response['ContentLength'],
                    content_type=response.get('ContentType'),
                    last_modified=response['LastModified'],
                    etag=response['ETag'].strip('"'),
                    version_id=response.get('VersionId'),
                    custom_metadata=custom_metadata
                )
        
        except ClientError as e:
            if e.response['Error']['Code'] in ['404', 'NoSuchKey']:
                return None
            raise Exception(f"Failed to get MinIO metadata: {str(e)}")
    
    async def list_files(
        self,
        prefix: Optional[str] = None,
        limit: Optional[int] = None
    ) -> List[FileMetadata]:
        """List files in MinIO bucket"""
        try:
            async with self._get_client() as s3:
                kwargs = {'Bucket': self._bucket_name}
                if prefix:
                    kwargs['Prefix'] = prefix
                if limit:
                    kwargs['MaxKeys'] = limit
                
                response = await s3.list_objects_v2(**kwargs)
                
                files = []
                for obj in response.get('Contents', []):
                    files.append(FileMetadata(
                        key=obj['Key'],
                        size=obj['Size'],
                        last_modified=obj['LastModified'],
                        etag=obj['ETag'].strip('"'),
                        custom_metadata={}  # Would need separate call to get metadata
                    ))
                
                return files
        
        except Exception as e:
            raise Exception(f"Failed to list MinIO files: {str(e)}")
    
    async def get_url(self, key: str, expires_in: int = 3600, method: str = "GET") -> str:
        """Generate MinIO presigned URL"""
        try:
            async with self._get_client() as s3:
                # Map method to boto3 operation
                operation_map = {
                    'GET': 'get_object',
                    'PUT': 'put_object',
                    'DELETE': 'delete_object'
                }
                
                operation = operation_map.get(method.upper(), 'get_object')
                
                url = await s3.generate_presigned_url(
                    operation,
                    Params={
                        'Bucket': self._bucket_name,
                        'Key': key
                    },
                    ExpiresIn=expires_in
                )
                return url
        except Exception as e:
            raise Exception(f"Failed to generate MinIO presigned URL: {str(e)}")
    
    async def copy(self, source_key: str, dest_key: str) -> bool:
        """MinIO server-side copy"""
        try:
            async with self._get_client() as s3:
                copy_source = {
                    'Bucket': self._bucket_name,
                    'Key': source_key
                }
                
                await s3.copy_object(
                    CopySource=copy_source,
                    Bucket=self._bucket_name,
                    Key=dest_key
                )
                
                return True
        except Exception as e:
            return False
    
    # MinIO-specific methods
    
    async def set_lifecycle_rules(self, rules: List[Dict[str, Any]]) -> bool:
        """Set MinIO bucket lifecycle rules"""
        try:
            async with self._get_client() as s3:
                await s3.put_bucket_lifecycle_configuration(
                    Bucket=self._bucket_name,
                    LifecycleConfiguration={'Rules': rules}
                )
                return True
        except Exception as e:
            raise Exception(f"Failed to set MinIO lifecycle rules: {str(e)}")
    
    async def enable_versioning(self) -> bool:
        """Enable versioning on MinIO bucket"""
        try:
            async with self._get_client() as s3:
                await s3.put_bucket_versioning(
                    Bucket=self._bucket_name,
                    VersioningConfiguration={'Status': 'Enabled'}
                )
                return True
        except Exception as e:
            raise Exception(f"Failed to enable MinIO versioning: {str(e)}")
