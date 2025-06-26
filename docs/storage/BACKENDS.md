# Storage Backend Technical Documentation

## Overview

Each storage backend is implemented independently with specialized features and optimizations. This document provides technical details for developers working with specific backends.

## Backend Architecture

### Independent Implementation Philosophy
- **Separate Files**: Each backend lives in its own file (`local_backend.py`, `minio_backend.py`, etc.)
- **Provider Specialization**: Each backend can implement provider-specific optimizations
- **Zero Dependencies**: Backends only load when needed and configured
- **Dynamic Loading**: Backends are loaded at runtime based on configuration

---

## 🗂️ Local Backend (`local_backend.py`)

### Technical Details
- **File**: `src/core/storage/backends/local_backend.py`
- **Dependencies**: None (uses Python standard library)
- **Storage**: Local filesystem with organized directory structure

### Directory Structure
```
./storage/
├── data/           # Actual file content
├── metadata/       # JSON metadata files  
└── versions/       # File version history
```

### Key Features
- **Automatic Versioning**: Each file modification creates a timestamped version
- **Metadata Storage**: Rich metadata stored as JSON alongside files
- **Soft Deletion**: Deleted files moved to versions directory
- **Development Optimized**: Fast access, easy debugging

### Configuration
```python
# Local backend configuration
LocalBackend.create_config(
    name="local",
    base_path="./storage"
)
```

### Specialized Methods
```python
# Get all versions of a file
versions = await backend.get_versions("users/123/resume.pdf")

# Update metadata without touching file
await backend.update_metadata("users/123/resume.pdf", {"job_id": "456"})
```

---

## 🗄️ MinIO Backend (`minio_backend.py`) 

### Technical Details
- **File**: `src/core/storage/backends/minio_backend.py`
- **Dependencies**: `aioboto3`, `boto3`, `botocore`
- **Protocol**: S3-compatible API with MinIO optimizations

### MinIO-Specific Optimizations
- **Path-Style Addressing**: Uses path-style URLs (required by MinIO)
- **Bucket Auto-Creation**: Automatically creates buckets if they don't exist
- **MinIO Features**: Lifecycle rules, versioning, server-side copy

### Configuration
```python
# MinIO backend configuration
MinIOBackend.create_config(
    name="minio",
    endpoint_url="http://your-minio:9000",
    access_key="your-access-key",
    secret_key="your-secret-key", 
    bucket_name="your-bucket",
    secure=False  # True for HTTPS
)
```

### MinIO-Specific Features
```python
# Enable versioning on bucket
await backend.enable_versioning()

# Set lifecycle rules
lifecycle_rules = [{
    'ID': 'DeleteOldVersions',
    'Status': 'Enabled',
    'NoncurrentVersionExpiration': {'NoncurrentDays': 30}
}]
await backend.set_lifecycle_rules(lifecycle_rules)

# Server-side copy (MinIO optimized)
await backend.copy("source/file.pdf", "dest/file.pdf")
```

### Performance Characteristics
- **Latency**: ~5-50ms (local network)
- **Throughput**: Multi-GB/s possible
- **Scalability**: Horizontal scaling with multiple MinIO nodes
- **Concurrent Operations**: Excellent for high-concurrency workloads

---

## ☁️ AWS S3 Backend (`aws_s3_backend.py`)

### Technical Details
- **File**: `src/core/storage/backends/aws_s3_backend.py`
- **Dependencies**: `aioboto3`, `boto3`, `botocore`
- **Provider**: Native AWS S3 with full AWS ecosystem integration

### AWS-Specific Features
- **Server-Side Encryption**: Automatic AES256 encryption
- **Storage Classes**: STANDARD, IA, GLACIER, DEEP_ARCHIVE
- **Intelligent Tiering**: Automatic cost optimization
- **AWS Integration**: CloudWatch, IAM, VPC endpoints

### Configuration
```python
# AWS S3 backend configuration
AWSS3Backend.create_config(
    name="aws_s3",
    access_key="AKIA...",
    secret_key="...",
    bucket_name="my-production-bucket",
    region="us-east-1",
    storage_class="STANDARD"
)
```

### AWS-Specific Methods
```python
# Transition to Glacier for archiving
await backend.transition_to_glacier("users/123/old_resume.pdf")

# Restore from Glacier (expedited)
await backend.restore_from_glacier("users/123/old_resume.pdf", days=1)

# Upload with intelligent tiering
extra_args = {'StorageClass': 'INTELLIGENT_TIERING'}
await backend.save(key, file, metadata, extra_args=extra_args)
```

### Storage Classes & Use Cases
- **STANDARD**: Frequently accessed data (< 30 days)
- **STANDARD_IA**: Infrequently accessed (30-90 days)
- **GLACIER**: Archive storage (90+ days)
- **DEEP_ARCHIVE**: Long-term archive (7+ years)
- **INTELLIGENT_TIERING**: Automatic optimization

### Performance Characteristics  
- **Latency**: 50-200ms (depending on region)
- **Throughput**: Virtually unlimited
- **Durability**: 99.999999999% (11 9's)
- **Availability**: 99.99%

---

## 🔷 Azure Blob Backend (`azure_blob_backend.py`)

### Technical Details
- **File**: `src/core/storage/backends/azure_blob_backend.py`
- **Dependencies**: `azure-storage-blob`
- **Provider**: Native Azure Blob Storage with Azure ecosystem integration

### Azure-Specific Features
- **Access Tiers**: Hot, Cool, Archive with automatic management
- **Azure Integration**: Active Directory, Key Vault, Monitor
- **Geo-Redundancy**: Built-in disaster recovery
- **Enterprise Features**: RBAC, compliance, governance

### Configuration
```python
# Azure Blob backend configuration
AzureBlobBackend.create_config(
    name="azure_blob",
    account_name="myaccount",
    account_key="...",
    container_name="resumes",
    tier="Hot"
)
```

### Azure-Specific Methods
```python
# Change access tier for cost optimization
await backend.set_blob_tier("users/123/old_resume.pdf", "Archive")

# Get blob properties with Azure metadata
properties = await backend.get_blob_properties("users/123/resume.pdf")
print(f"Tier: {properties.blob_tier}")
print(f"Access time: {properties.last_accessed_on}")

# Set blob metadata
await backend.set_blob_metadata("users/123/resume.pdf", {
    "department": "engineering",
    "classification": "internal"
})
```

### Access Tiers & Performance
- **Hot**: Frequent access, highest storage cost, lowest access cost
- **Cool**: Infrequent access (30+ days), lower storage cost
- **Archive**: Rare access (180+ days), lowest storage cost, higher access cost

### Performance Characteristics
- **Latency**: 20-100ms (depending on tier and region)
- **Throughput**: Multi-GB/s
- **Durability**: 99.999999999% (11 9's) with geo-redundancy
- **Availability**: 99.9% (Hot), 99% (Cool), 99% (Archive)

---

## Backend Comparison Matrix

| Feature | Local | MinIO | AWS S3 | Azure Blob |
|---------|-------|-------|--------|------------|
| **Development** | ✅ Perfect | ⚡ Good | 💰 Expensive | 💰 Expensive |
| **Testing/Staging** | 🔄 Limited | ✅ Perfect | ⚡ Good | ⚡ Good |
| **Production** | ❌ No | ✅ Excellent | ✅ Excellent | ✅ Excellent |
| **Cost** | 🆓 Free | 💚 Low | 💛 Variable | 💛 Variable |
| **Latency** | ⚡ <5ms | ⚡ 5-50ms | 🌐 50-200ms | 🌐 20-100ms |
| **Scalability** | ❌ Single node | ✅ Horizontal | ♾️ Unlimited | ♾️ Unlimited |
| **Durability** | 💾 Disk-dependent | 🔄 Multi-node | 🛡️ 11 9's | 🛡️ 11 9's |

---

## Backend Selection Guide

### Choose **Local** when:
- Developing locally
- Running tests
- Quick prototyping
- No network dependencies needed

### Choose **MinIO** when:
- Need S3 compatibility
- Want cost-effective object storage
- Running in private cloud/datacenter
- Need high performance with control

### Choose **AWS S3** when:
- Using AWS ecosystem
- Need Glacier archiving
- Want intelligent tiering
- Require maximum scalability

### Choose **Azure Blob** when:
- Using Azure ecosystem
- Need enterprise compliance features
- Want built-in geo-redundancy
- Require Azure AD integration

---

## Development Guidelines

### Adding New Backends

1. **Create Backend File**: `src/core/storage/backends/your_backend.py`
2. **Implement Interface**: Extend `StorageBackend` base class
3. **Add to Registry**: Update `BackendRegistry._backend_modules`
4. **Add Dependencies**: Update `pyproject.toml`
5. **Add Configuration**: Update settings and .env.example
6. **Write Tests**: Create comprehensive test suite
7. **Document**: Add to this file with technical details

### Backend Implementation Requirements

```python
class YourBackend(StorageBackend):
    """Your storage backend implementation"""
    
    @classmethod
    def create_config(cls, name: str, **kwargs) -> BackendConfig:
        """Create backend configuration"""
        
    async def initialize(self) -> bool:
        """Initialize backend connection"""
        
    async def health_check(self) -> bool:
        """Check backend health"""
        
    async def save(self, key: str, file: BinaryIO, metadata: Dict) -> Dict:
        """Save file with metadata"""
        
    async def retrieve(self, key: str) -> BinaryIO:
        """Retrieve file content"""
        
    async def delete(self, key: str) -> bool:
        """Delete file"""
        
    async def exists(self, key: str) -> bool:
        """Check if file exists"""
        
    async def get_metadata(self, key: str) -> Optional[FileMetadata]:
        """Get file metadata"""
        
    async def list_files(self, prefix: str, limit: int) -> List[FileMetadata]:
        """List files with prefix"""
        
    async def get_url(self, key: str, expires_in: int) -> str:
        """Get temporary access URL"""
```

### Best Practices

1. **Error Handling**: Always wrap provider-specific errors
2. **Logging**: Use structured logging with correlation IDs
3. **Configuration**: Validate all required settings in `initialize()`
4. **Performance**: Implement async/await properly
5. **Security**: Never log credentials or sensitive data
6. **Testing**: Mock external services for unit tests
7. **Documentation**: Document provider-specific features clearly

---

## Troubleshooting

### Common Issues by Backend

#### Local Backend
- **Permission errors**: Check filesystem permissions
- **Disk space**: Monitor available disk space
- **File locks**: Handle concurrent access properly

#### MinIO Backend  
- **Connection refused**: Verify MinIO server is running
- **Bucket not found**: Enable auto-creation or create manually
- **Path style**: Ensure path-style addressing is used

#### AWS S3 Backend
- **Credentials**: Verify AWS access keys and permissions
- **Region mismatch**: Ensure bucket region matches configuration
- **Rate limiting**: Implement exponential backoff

#### Azure Blob Backend
- **Authentication**: Check account name and key
- **Container not found**: Ensure container exists
- **Access tier**: Verify tier transitions are allowed

### Debug Mode

Enable detailed logging for any backend:

```python
import logging
logging.basicConfig(level=logging.DEBUG)

# Test specific backend
from src.core.storage.manager import BackendRegistry
backend_class = BackendRegistry._load_backend_class('minio')
backend = backend_class(config)
await backend.initialize()
```