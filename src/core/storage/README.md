# Storage Service - Resume Automation Platform

## Overview

The Storage Service is a critical component of the Resume Automation Platform, providing a unified, enterprise-ready abstraction layer for file storage operations. Built with complete backend independence and dynamic loading, it enables seamless switching between storage backends with zero code changes - only configuration updates needed.

## Key Design Principles

### ✅ **Complete Backend Independence**
- Each storage backend is implemented in its own dedicated file
- Backends can be highly specialized with provider-specific optimizations
- No shared code between backends except the base interface
- Full technical depth available for each provider

### ✅ **Dynamic Backend Loading**
- Backends are loaded dynamically based on configuration
- Missing dependencies are handled gracefully with helpful error messages
- No hard-coded imports or compilation dependencies
- Automatic fallback and error handling

### ✅ **Configuration-Only Switching**
- Switch between any backend by changing `.env` file only
- No code changes, rebuilds, or deployments required
- Instant backend switching for development and production

## Backend Architecture

### Independent Backend System
```
Application → SimpleStorageService → StorageManager
                                          │
                                          ▼
                                 Dynamic Backend Loading
                                          │
        ┌─────────────────────────────────┼─────────────────────────────────┐
        │                                 │                                 │
        ▼                                 ▼                                 ▼
┌──────────────┐                 ┌──────────────┐                 ┌──────────────┐
│ Local Backend│                 │ MinIO Backend│                 │ AWS S3 Backend│
│              │                 │              │                 │              │
│ • File I/O   │                 │ • S3 API     │                 │ • Native AWS │
│ • Versioning │                 │ • MinIO Opts │                 │ • Glacier    │
│ • Metadata   │                 │ • Presigned  │                 │ • Encryption │
└──────────────┘                 └──────────────┘                 └──────────────┘
        │                                 │                                 │
        ▼                                 ▼                                 ▼
   Local Files                      MinIO Server                      AWS S3 Service

┌──────────────┐
│Azure Backend │
│              │
│ • Blob Tiers │
│ • Azure Opts │
│ • Hot/Cool   │
└──────────────┘
        │
        ▼
 Azure Blob Storage
```

### Configuration-Driven Selection
```bash
# .env file controls everything
PRIMARY_BACKEND=minio  # or local, aws_s3, azure_blob

# Backend-specific configuration
MINIO_ENDPOINT_URL=http://your-server:9000
MINIO_ACCESS_KEY=your-key
MINIO_SECRET_KEY=your-secret
MINIO_BUCKET_NAME=your-bucket
```

## Core Design Principles

### 1. Simplicity First
The application interface (`SimpleStorageService`) exposes only essential operations:
- `save()` - Store a file
- `retrieve()` - Get a file
- `delete()` - Remove a file
- `get_download_url()` - Generate temporary access URL

### 2. Backend Agnostic
Applications never interact with storage backends directly. The storage layer handles:
- Backend selection and routing
- Connection management
- Error handling and retries
- Migration between backends

### 3. Enterprise Security
- **User Isolation**: Files automatically namespaced by user ID
- **Access Control**: Built-in ownership verification
- **Audit Trail**: Comprehensive metadata tracking
- **Encryption Ready**: Backend-specific encryption support

### 4. Zero-Downtime Migration
- Live migration between backends without service interruption
- Batch and parallel migration support
- Progress tracking and rollback capabilities

## Key Features

### Backend Support Matrix

| Backend | Status | Use Case | Specializations | Dependencies |
|---------|--------|----------|-----------------|--------------|
| **Local** | ✅ Ready | Development | File I/O, Versioning, Metadata | None |
| **MinIO** | ✅ Ready | Testing/Staging | S3 API, MinIO optimizations, Presigned URLs | aioboto3, boto3 |
| **AWS S3** | ✅ Ready | Production | Glacier, Intelligent Tiering, AWS encryption | aioboto3, boto3 |
| **Azure Blob** | ✅ Ready | Enterprise/Backup | Hot/Cool/Archive tiers, Azure integration | azure-storage-blob |
| **GCS** | 🔄 Future | Alternative | Multi-region, CDN integration | google-cloud-storage |

### Backend Independence Features

| Feature | Local | MinIO | AWS S3 | Azure |
|---------|-------|-------|--------|-------|
| **Specialized Implementation** | ✅ | ✅ | ✅ | ✅ |
| **Provider-Specific Optimizations** | ✅ | ✅ | ✅ | ✅ |
| **Independent Configuration** | ✅ | ✅ | ✅ | ✅ |
| **Dynamic Loading** | ✅ | ✅ | ✅ | ✅ |
| **Graceful Dependency Handling** | ✅ | ✅ | ✅ | ✅ |

### Storage Tiers (Future Implementation)

Following the STORAGE.md strategy:

```python
class StorageTier(Enum):
    HOT = "hot"        # < 100ms access, active files
    WARM = "warm"      # < 1s access, recent files  
    COLD = "cold"      # Minutes, archived files
    GLACIER = "glacier" # Hours, compliance/backup
```

### Enterprise Features

#### 1. High Availability
- Multiple backend support with automatic failover
- Health checking and circuit breaking
- Retry logic with exponential backoff

#### 2. Performance Optimization
- Connection pooling for cloud backends
- Parallel upload/download for large files
- Intelligent caching layer (Redis integration ready)

#### 3. Monitoring & Observability
- Structured logging with correlation IDs
- Metrics collection (ready for Prometheus)
- Storage usage tracking per user/tier

#### 4. Compliance & Governance
- Retention policy support
- Automated lifecycle management
- Audit logging for all operations
- GDPR-compliant data deletion

## Implementation Details

### Core Components

#### 1. SimpleStorageService (`storage_service.py`)
The application-facing interface that provides dead-simple file operations.

```python
# Example usage
from src.services.storage_service import storage

# Save a file
file_id = await storage.save(
    file=pdf_content,
    filename="resume.pdf",
    user_id=user.id,
    metadata={"job_id": "123"}
)

# Retrieve a file
file_data = await storage.retrieve(file_id, user.id)

# Get download URL
url = await storage.get_download_url(file_id, user.id)
```

#### 2. StorageManager (`manager.py`)
Orchestrates backend operations and handles routing logic.

- Backend initialization and health monitoring
- Request routing based on configuration
- Migration coordination
- Failover handling

#### 3. Storage Backends (`backends/`)
Pluggable backend implementations following a common interface.

```python
class StorageBackend(ABC):
    async def save(key, file, metadata) -> Dict
    async def retrieve(key) -> BinaryIO
    async def delete(key) -> bool
    async def exists(key) -> bool
    async def get_metadata(key) -> FileMetadata
    async def list_files(prefix, limit) -> List[FileMetadata]
```

#### 4. Migration System (`backends/migration.py`)
Zero-downtime migration between storage backends.

```python
# Migrate specific files
migrator = StorageMigrator(source_backend, target_backend)
result = await migrator.migrate_file("users/123/resume.pdf")

# Bulk migration with filtering
results = await migrator.migrate_all(
    filter_criteria={"prefix": "users/123/"},
    delete_source=True,
    batch_size=100
)
```

### Configuration

#### Development
```python
BACKENDS_CONFIG = {
    "local": {
        "type": "local",
        "base_path": "./storage"
    }
}
PRIMARY_BACKEND = "local"
```

#### Production (Multi-Backend)
```python
BACKENDS_CONFIG = {
    "aws_hot": {
        "type": "aws_s3",
        "bucket_name": "myapp-hot",
        "region": "us-east-1",
        "storage_class": "STANDARD"
    },
    "aws_cold": {
        "type": "aws_s3",
        "bucket_name": "myapp-archive",
        "region": "us-east-1",
        "storage_class": "GLACIER"
    },
    "azure_backup": {
        "type": "azure_blob",
        "container_name": "backup",
        "tier": "Archive"
    }
}
PRIMARY_BACKEND = "aws_hot"
```

### Error Handling

The service implements comprehensive error handling:

1. **Automatic Retries**: Transient failures are retried with exponential backoff
2. **Graceful Degradation**: Falls back to available backends if primary fails
3. **Clear Error Messages**: Application receives actionable error information
4. **Circuit Breaking**: Prevents cascading failures by temporarily disabling unhealthy backends

### Security Considerations

1. **Access Control**
   - User-based file namespacing
   - Ownership verification on all operations
   - Temporary signed URLs with expiration

2. **Data Protection**
   - Backend-specific encryption at rest
   - TLS for data in transit
   - Secure credential management

3. **Audit & Compliance**
   - All operations logged with user context
   - File access tracking
   - Retention policy enforcement

## Usage Examples

### Basic File Operations
```python
# In your API endpoint
@router.post("/upload")
async def upload_file(
    file: UploadFile,
    current_user: User = Depends(get_current_user)
):
    file_id = await storage.save(
        file=file,
        filename=file.filename,
        user_id=current_user.id
    )
    return {"file_id": file_id}

@router.get("/download/{file_id}")
async def download_file(
    file_id: str,
    current_user: User = Depends(get_current_user)
):
    url = await storage.get_download_url(
        file_id=file_id,
        user_id=current_user.id
    )
    return {"download_url": url}
```

### Resume Generation Integration
```python
async def generate_resume(user_id: int, job_data: dict):
    # Generate PDF
    pdf_content = await create_pdf(job_data)
    
    # Save it - storage handles everything
    file_id = await storage.save(
        file=pdf_content,
        filename=f"resume_{job_data['id']}.pdf",
        user_id=user_id,
        metadata={"job_id": str(job_data['id'])}
    )
    
    return file_id
```

## Backend Switching Guide

### 🔄 **Instant Backend Switching**

Switch between any backend with zero code changes - only configuration updates:

#### 1. Switch to Your MinIO Server
```bash
# .env file
PRIMARY_BACKEND=minio
MINIO_ENDPOINT_URL=http://your-minio-server:9000
MINIO_ACCESS_KEY=your-access-key
MINIO_SECRET_KEY=your-secret-key
MINIO_BUCKET_NAME=your-bucket-name
MINIO_SECURE=false
```

#### 2. Switch to Local Development
```bash
# .env file
PRIMARY_BACKEND=local
LOCAL_STORAGE_PATH=./storage
```

#### 3. Switch to AWS S3 Production
```bash
# .env file
PRIMARY_BACKEND=aws_s3
AWS_ACCESS_KEY_ID=your-aws-access-key
AWS_SECRET_ACCESS_KEY=your-aws-secret-key
AWS_S3_BUCKET_NAME=your-s3-bucket
AWS_REGION=us-east-1
AWS_S3_STORAGE_CLASS=STANDARD
```

#### 4. Switch to Azure Blob Storage
```bash
# .env file
PRIMARY_BACKEND=azure_blob
AZURE_ACCOUNT_NAME=your-account-name
AZURE_ACCOUNT_KEY=your-account-key
AZURE_CONTAINER_NAME=your-container
AZURE_BLOB_TIER=Hot
```

### 🔍 **Backend Status Checking**

Check which backends are available and configured:

```python
from src.core.storage.manager import StorageManager, BackendRegistry

# List all available backends
available = BackendRegistry.list_available_backends()
print(f"Available backends: {available}")

# Get detailed backend information  
for backend_type in BackendRegistry.list_all_backends():
    info = BackendRegistry.get_backend_info(backend_type)
    print(f"{backend_type}: {info['status']}")

# Check current storage configuration
manager = StorageManager()
backends = manager.list_backends()
for name, info in backends.items():
    primary = "🎯" if info['is_primary'] else "  "
    print(f"{primary} {name}: {info['type']} ({info['status']})")
```

### 📦 **Dependency Management**

Each backend manages its own dependencies independently:

```bash
# All backends pre-installed (recommended)
poetry install

# Install specific backend dependencies if needed
poetry add aioboto3 boto3 botocore        # MinIO + AWS S3
poetry add azure-storage-blob              # Azure Blob
poetry add google-cloud-storage            # Future: GCS
```

Missing dependencies are handled gracefully with helpful error messages.

## Performance Characteristics

### Local Backend
- **Latency**: < 5ms
- **Throughput**: Limited by disk I/O
- **Scalability**: Single server only

### MinIO Backend
- **Latency**: < 50ms (local network)
- **Throughput**: 10GB/s+ possible
- **Scalability**: Horizontal scaling

### AWS S3 Backend
- **Latency**: 50-200ms
- **Throughput**: Virtually unlimited
- **Scalability**: Infinite

## Monitoring & Metrics

### Key Metrics to Track
- Storage operations per second
- Average operation latency
- Storage usage by user/tier
- Failed operations count
- Migration progress

### Health Checks
```python
# Built-in health check endpoint
GET /health/storage

Response:
{
    "backends": {
        "local": {"healthy": true, "latency_ms": 2},
        "minio": {"healthy": true, "latency_ms": 45}
    },
    "primary_backend": "local",
    "total_files": 15234,
    "total_size_gb": 45.2
}
```

## Backend-Specific Features

### 🗂️ **Local Backend** (`local_backend.py`)
- **Versioning**: Automatic file versioning with timestamps
- **Metadata**: JSON metadata storage alongside files
- **Development**: Perfect for local development and testing
- **No Dependencies**: Works out of the box

### 🗄️ **MinIO Backend** (`minio_backend.py`)
- **S3 Compatibility**: Full S3 API compatibility
- **MinIO Optimizations**: Path-style addressing, MinIO-specific features
- **Presigned URLs**: Secure temporary access URLs
- **Bucket Management**: Automatic bucket creation and lifecycle rules

### ☁️ **AWS S3 Backend** (`aws_s3_backend.py`)
- **Native AWS Features**: Intelligent Tiering, Glacier transitions
- **AWS Encryption**: Server-side encryption with AES256
- **Storage Classes**: STANDARD, IA, GLACIER, DEEP_ARCHIVE
- **AWS Integration**: CloudWatch metrics, IAM policies

### 🔷 **Azure Blob Backend** (`azure_blob_backend.py`)
- **Blob Tiers**: Hot, Cool, Archive tier management
- **Azure Integration**: Native Azure authentication and monitoring
- **Geo-Redundancy**: Built-in disaster recovery options
- **Enterprise Features**: Azure AD integration, compliance

## Future Enhancements

### Phase 2 (Next)
- Redis caching layer for frequently accessed files
- Advanced lifecycle management with ML predictions
- CDN integration for public file serving

### Phase 3 (Planned)
- Google Cloud Storage backend
- Multi-region replication strategies
- Real-time storage analytics dashboard
- Cost optimization algorithms

### Phase 4 (Vision)
- ML-based predictive caching
- Automated tier optimization
- Global content distribution
- Advanced security scanning

## Troubleshooting

### Common Issues

1. **"Backend not available" errors**
   - Check backend health: `GET /health/storage`
   - Verify credentials and network connectivity
   - Check logs for initialization errors

2. **Slow file uploads**
   - Enable parallel uploads for large files
   - Check network bandwidth
   - Consider using presigned URLs for direct uploads

3. **Migration failures**
   - Verify source files exist
   - Check target backend has sufficient space
   - Review migration logs for specific errors

### Debug Mode
```python
# Enable debug logging
export LOG_LEVEL=DEBUG
export STORAGE_DEBUG=true

# Test specific backend
python -m src.core.storage.test --backend local
```

## Contributing

When adding new storage backends:

1. Implement the `StorageBackend` abstract class
2. Add backend to `BackendRegistry`
3. Write integration tests
4. Update documentation
5. Add migration support

## License

Part of the Resume Automation Platform. See main LICENSE file.

Suggestion - Something to think about:
# Add structured error types for better error handling
class StorageError(Exception):
    pass

class QuotaExceededError(StorageError):
    pass

# Consider adding batch operations for performance
async def save_batch(self, files: List[FileUpload]) -> List[str]:
    """Save multiple files in parallel"""
    pass


Benefits of Storage-Event Integration
1. Decoupled Architecture
Storage operations don't need to know about business logic
New features can be added by simply subscribing to events
Easy to test components in isolation
2. Automatic Workflows
When a resume is uploaded:

Text extraction happens automatically
Job matching triggers immediately
Analytics are updated in real-time
No manual coordination needed
3. Better User Experience
Fast uploads (processing happens async)
Real-time notifications
Progress tracking through events
Automatic retries on failures
4. Powerful Analytics
Track everything automatically:

Upload/download patterns
Storage usage trends
Error rates and types
Performance metrics
5. Compliance & Auditing
Complete audit trail of all operations
Easy compliance reporting
Data retention policies enforced automatically
Access patterns tracked
6. Scalability
Event handlers can run on separate workers
Easy to add more processing power
Workflows can be distributed
No bottlenecks in main application
7. Use Cases for Resume Automation
On Resume Upload:

Extract text for searching
Parse skills and experience
Match against open positions
Queue for application submission
Update user's profile
On Storage Quota Exceeded:

Notify user
Suggest cleanup options
Offer upgrade path
Prevent new uploads
On File Access:

Track which resumes are viewed
Analyze successful applications
Optimize resume templates
Detect unusual access patterns
The event system transforms storage from a simple file store into an intelligent, reactive system that drives your entire application workflow!
