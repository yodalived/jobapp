"""
Azure Blob Storage backend
"""

from azure.storage.blob.aio import BlobServiceClient
from azure.storage.blob import BlobProperties
from typing import BinaryIO, Optional, List, Dict, Any
import io

from .base import StorageBackend, BackendConfig, BackendCapability


class AzureBlobBackend(StorageBackend):
    """Azure Blob Storage backend"""
    
    @classmethod
    def create_config(
        cls,
        name: str,
        account_name: str,
        account_key: str,
        container_name: str,
        tier: str = "Hot"
    ) -> BackendConfig:
        """Create an Azure Blob backend configuration"""
        return BackendConfig(
            name=name,
            backend_type="azure_blob",
            capabilities=[
                BackendCapability.VERSIONING,
                BackendCapability.ENCRYPTION,
                BackendCapability.LIFECYCLE_RULES,
                BackendCapability.TAGGING,
                BackendCapability.SIGNED_URLS,
            ],
            config={
                "account_name": account_name,
                "account_key": account_key,
                "container_name": container_name,
                "tier": tier
            }
        )
    
    def _validate_config(self) -> None:
        """Validate Azure configuration"""
        required = ["account_name", "account_key", "container_name"]
        for field in required:
            if field not in self.config.config:
                raise ValueError(f"Missing required config field: {field}")
    
    def _initialize(self) -> None:
        """Initialize Azure connection"""
        conn_str = (
            f"DefaultEndpointsProtocol=https;"
            f"AccountName={self.config.config['account_name']};"
            f"AccountKey={self.config.config['account_key']};"
            f"EndpointSuffix=core.windows.net"
        )
        self._service_client = BlobServiceClient.from_connection_string(conn_str)
        self._container_name = self.config.config["container_name"]
        self._tier = self.config.config.get("tier", "Hot")
    
    async def upload(self, key: str, file: BinaryIO, metadata: Optional[Dict[str, str]] = None) -> Dict[str, Any]:
        """Upload to Azure Blob Storage"""
        try:
            blob_client = self._service_client.get_blob_client(
                container=self._container_name,
                blob=key
            )
            
            file.seek(0)
            
            # Azure-specific upload options
            await blob_client.upload_blob(
                data=file,
                metadata=metadata,
                standard_blob_tier=self._tier,
                overwrite=True
            )
            
            # Get properties
            properties = await blob_client.get_blob_properties()
            
            return {
                "key": key,
                "etag": properties.etag,
                "size": properties.size,
                "tier": properties.blob_tier,
                "last_modified": properties.last_modified.isoformat(),
                "backend": self.name
            }
        
        except Exception as e:
            raise Exception(f"Azure Blob upload failed: {str(e)}")
    
    # Azure-specific methods
    
    async def set_blob_tier(self, key: str, tier: str) -> bool:
        """Change blob access tier (Hot, Cool, Archive)"""
        try:
            blob_client = self._service_client.get_blob_client(
                container=self._container_name,
                blob=key
            )
            await blob_client.set_standard_blob_tier(tier)
            return True
        except Exception as e:
            raise Exception(f"Failed to set blob tier: {str(e)}")
