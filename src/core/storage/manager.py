"""
Simplified storage manager that delegates all logic to backends
"""

from typing import Dict, Any, BinaryIO, Optional, List
from enum import Enum
import logging

from .backends.base import StorageBackend, BackendConfig
from .backends.migration import StorageMigrator
from src.core.config import settings
import importlib

logger = logging.getLogger(__name__)


class BackendType(Enum):
    """Available backend types"""
    MINIO = "minio"
    AWS_S3 = "aws_s3"
    AZURE_BLOB = "azure_blob"
    GCS = "gcs"
    LOCAL = "local"


class BackendRegistry:
    """Registry of available storage backends with dynamic loading"""
    
    # Map backend types to their module/class information
    _backend_modules = {
        BackendType.LOCAL.value: {
            'module': 'src.core.storage.backends.local_backend',
            'class': 'LocalBackend',
            'dependencies': []  # No extra dependencies needed
        },
        BackendType.MINIO.value: {
            'module': 'src.core.storage.backends.minio_backend', 
            'class': 'MinIOBackend',
            'dependencies': ['aioboto3', 'boto3', 'botocore']
        },
        BackendType.AWS_S3.value: {
            'module': 'src.core.storage.backends.aws_s3_backend',
            'class': 'AWSS3Backend', 
            'dependencies': ['aioboto3', 'boto3', 'botocore']
        },
        BackendType.AZURE_BLOB.value: {
            'module': 'src.core.storage.backends.azure_blob_backend',
            'class': 'AzureBlobBackend',
            'dependencies': ['azure-storage-blob']
        }
    }
    
    @classmethod
    def _load_backend_class(cls, backend_type: str) -> type[StorageBackend]:
        """Dynamically load backend class"""
        if backend_type not in cls._backend_modules:
            raise ValueError(f"Unknown backend type: {backend_type}")
        
        backend_info = cls._backend_modules[backend_type]
        
        try:
            # Import the module
            module = importlib.import_module(backend_info['module'])
            # Get the class
            backend_class = getattr(module, backend_info['class'])
            return backend_class
        except ImportError as e:
            missing_deps = ", ".join(backend_info['dependencies'])
            raise ImportError(
                f"Cannot load {backend_type} backend. "
                f"Missing dependencies: {missing_deps}. "
                f"Install with: poetry add {' '.join(backend_info['dependencies'])}"
            ) from e
        except AttributeError as e:
            raise ValueError(f"Backend class {backend_info['class']} not found in {backend_info['module']}") from e
    
    @classmethod
    def create_backend(cls, config: BackendConfig) -> StorageBackend:
        """Create a backend instance from configuration"""
        backend_class = cls._load_backend_class(config.backend_type)
        return backend_class(config)
    
    @classmethod
    def list_available_backends(cls) -> List[str]:
        """List all backend types that can be loaded (with dependencies)"""
        available = []
        for backend_type in cls._backend_modules.keys():
            try:
                cls._load_backend_class(backend_type)
                available.append(backend_type)
            except ImportError:
                continue
        return available
    
    @classmethod
    def list_all_backends(cls) -> List[str]:
        """List all defined backend types (regardless of dependencies)"""
        return list(cls._backend_modules.keys())
    
    @classmethod
    def get_backend_info(cls, backend_type: str) -> Dict[str, Any]:
        """Get information about a backend type"""
        if backend_type not in cls._backend_modules:
            raise ValueError(f"Unknown backend type: {backend_type}")
        
        backend_info = cls._backend_modules[backend_type].copy()
        
        # Check if backend is available
        try:
            cls._load_backend_class(backend_type)
            backend_info['available'] = True
            backend_info['status'] = 'ready'
        except ImportError as e:
            backend_info['available'] = False
            backend_info['status'] = f'missing dependencies: {str(e)}'
        
        return backend_info


class StorageManager:
    """
    Simplified storage manager that only handles backend routing.
    All storage logic is delegated to the backends themselves.
    """
    
    def __init__(self):
        self._backends: Dict[str, StorageBackend] = {}
        self._primary_backend: Optional[str] = None
        self._initialized = False
    
    async def _ensure_initialized(self):
        """Ensure the storage manager is initialized"""
        if not self._initialized:
            await self._initialize_backends()
    
    async def _initialize_backends(self):
        """Initialize configured backends from settings"""
        # Load backend configurations from settings
        backend_configs = self._load_backend_configs()
        
        for name, config in backend_configs.items():
            try:
                backend = BackendRegistry.create_backend(config)
                # Initialize the backend
                init_success = await backend.initialize()
                if init_success:
                    self._backends[name] = backend
                    logger.info(f"Initialized backend: {name} ({config.backend_type})")
                else:
                    logger.error(f"Failed to initialize backend {name}: initialization returned False")
            except Exception as e:
                logger.error(f"Failed to initialize backend {name}: {e}")
        
        # Set primary backend
        self._primary_backend = settings.primary_backend
        if self._primary_backend not in self._backends:
            raise ValueError(f"Primary backend '{self._primary_backend}' not found")
        
        self._initialized = True
    
    def _load_backend_configs(self) -> Dict[str, BackendConfig]:
        """Load backend configurations from settings dynamically"""
        configs = {}
        
        # Local backend (always available)
        try:
            LocalBackend = BackendRegistry._load_backend_class('local')
            configs['local'] = LocalBackend.create_config(
                name="local",
                base_path=settings.local_storage_path
            )
            logger.info("Local backend configured")
        except Exception as e:
            logger.error(f"Failed to configure local backend: {e}")
        
        # MinIO backend (if configured)
        if settings.minio_config:
            try:
                MinIOBackend = BackendRegistry._load_backend_class('minio')
                config = settings.minio_config
                configs['minio'] = MinIOBackend.create_config(
                    name="minio",
                    endpoint_url=config["endpoint_url"],
                    access_key=config["access_key"],
                    secret_key=config["secret_key"],
                    bucket_name=config["bucket_name"],
                    secure=config.get("secure", False)
                )
                logger.info("MinIO backend configured")
            except ImportError as e:
                logger.warning(f"MinIO config found but dependencies not available: {e}")
            except Exception as e:
                logger.error(f"Failed to configure MinIO backend: {e}")
        
        # AWS S3 backend (if configured)
        if settings.aws_s3_config:
            try:
                AWSS3Backend = BackendRegistry._load_backend_class('aws_s3')
                config = settings.aws_s3_config
                configs['aws_s3'] = AWSS3Backend.create_config(
                    name="aws_s3",
                    access_key=config["access_key"],
                    secret_key=config["secret_key"],
                    bucket_name=config["bucket_name"],
                    region=config["region"],
                    storage_class=config.get("storage_class", "STANDARD")
                )
                logger.info("AWS S3 backend configured")
            except ImportError as e:
                logger.warning(f"AWS S3 config found but dependencies not available: {e}")
            except Exception as e:
                logger.error(f"Failed to configure AWS S3 backend: {e}")
        
        # Azure Blob backend (if configured)
        if settings.azure_blob_config:
            try:
                AzureBlobBackend = BackendRegistry._load_backend_class('azure_blob')
                config = settings.azure_blob_config
                configs['azure_blob'] = AzureBlobBackend.create_config(
                    name="azure_blob",
                    account_name=config["account_name"],
                    account_key=config["account_key"],
                    container_name=config["container_name"],
                    tier=config.get("tier", "Hot")
                )
                logger.info("Azure Blob backend configured")
            except ImportError as e:
                logger.warning(f"Azure Blob config found but dependencies not available: {e}")
            except Exception as e:
                logger.error(f"Failed to configure Azure Blob backend: {e}")
        
        return configs
    
    def get_backend(self, name: Optional[str] = None) -> StorageBackend:
        """Get a specific backend or the primary one"""
        backend_name = name or self._primary_backend
        backend = self._backends.get(backend_name)
        
        if not backend:
            raise ValueError(f"Backend '{backend_name}' not found")
        
        return backend
    
    async def save(
        self,
        key: str,
        file: BinaryIO,
        metadata: Optional[Dict[str, str]] = None,
        backend: Optional[str] = None
    ) -> Dict[str, Any]:
        """
        Save a file to storage.
        
        The backend handles all the complexity - this just routes the request.
        """
        await self._ensure_initialized()
        storage_backend = self.get_backend(backend)
        result = await storage_backend.save(key, file, metadata)
        
        # Add which backend was used
        result['backend_name'] = storage_backend.name
        return result
    
    async def retrieve(
        self,
        key: str,
        backend: Optional[str] = None
    ) -> BinaryIO:
        """Retrieve a file from storage"""
        await self._ensure_initialized()
        storage_backend = self.get_backend(backend)
        return await storage_backend.retrieve(key)
    
    async def delete(
        self,
        key: str,
        backend: Optional[str] = None
    ) -> bool:
        """Delete a file from storage"""
        await self._ensure_initialized()
        storage_backend = self.get_backend(backend)
        return await storage_backend.delete(key)
    
    async def exists(
        self,
        key: str,
        backend: Optional[str] = None
    ) -> bool:
        """Check if a file exists"""
        storage_backend = self.get_backend(backend)
        return await storage_backend.exists(key)
    
    async def get_metadata(
        self,
        key: str,
        backend: Optional[str] = None
    ) -> Dict[str, Any]:
        """Get file metadata"""
        storage_backend = self.get_backend(backend)
        return await storage_backend.get_metadata(key)
    
    async def get_url(
        self,
        key: str,
        expires_in: int = 3600,
        backend: Optional[str] = None
    ) -> str:
        """Get a temporary URL for file access"""
        await self._ensure_initialized()
        storage_backend = self.get_backend(backend)
        return await storage_backend.get_url(key, expires_in)
    
    # Migration support
    
    def create_migrator(
        self,
        source_backend: str,
        target_backend: str,
        db_session_factory
    ) -> StorageMigrator:
        """Create a migrator between two backends"""
        source = self.get_backend(source_backend)
        target = self.get_backend(target_backend)
        
        return StorageMigrator(source, target, db_session_factory)
    
    async def migrate_file(
        self,
        key: str,
        source_backend: str,
        target_backend: str,
        delete_source: bool = False
    ) -> Dict[str, Any]:
        """Migrate a single file between backends"""
        source = self.get_backend(source_backend)
        target = self.get_backend(target_backend)
        
        # Export from source
        export_data = await source.export_file(key)
        
        # Import to target
        new_key = await target.import_file(export_data)
        
        # Delete from source if requested
        if delete_source:
            await source.delete(key)
        
        return {
            "old_key": key,
            "new_key": new_key,
            "source_backend": source_backend,
            "target_backend": target_backend,
            "deleted_source": delete_source
        }
    
    # Backend management
    
    def list_backends(self) -> Dict[str, Dict[str, Any]]:
        """List all configured backends and their capabilities"""
        backend_info = {}
        
        # Add configured backends
        for name, backend in self._backends.items():
            backend_info[name] = {
                "type": backend.config.backend_type,
                "capabilities": [cap.value for cap in backend.capabilities],
                "is_primary": name == self._primary_backend,
                "status": "configured"
            }
        
        # Add available but not configured backends
        available_types = BackendRegistry.list_available_backends()
        for backend_type in available_types:
            if backend_type not in [b.config.backend_type for b in self._backends.values()]:
                registry_info = BackendRegistry.get_backend_info(backend_type)
                backend_info[f"{backend_type}_available"] = {
                    "type": backend_type,
                    "capabilities": "unknown",
                    "is_primary": False,
                    "status": "available_but_not_configured",
                    "dependencies": registry_info.get('dependencies', [])
                }
        
        return backend_info
    
    def switch_primary_backend(self, backend_name: str):
        """Switch the primary backend"""
        if backend_name not in self._backends:
            raise ValueError(f"Backend '{backend_name}' not found")
        
        self._primary_backend = backend_name
        logger.info(f"Switched primary backend to: {backend_name}")
