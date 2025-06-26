# Storage Documentation

## Overview

The Resume Automation Platform uses an independent storage backend architecture that allows switching between storage providers with zero code changes.

## Documentation Structure

- **[BACKENDS.md](./BACKENDS.md)** - Technical details for each storage backend
- **[Main Storage README](../../src/core/storage/README.md)** - Complete architecture documentation

## Quick Start

### Switch Storage Backend

Simply update your `.env` file:

```bash
# Use your MinIO server
PRIMARY_BACKEND=minio
MINIO_ENDPOINT_URL=http://your-minio-server:9000
MINIO_ACCESS_KEY=your-key
MINIO_SECRET_KEY=your-secret
MINIO_BUCKET_NAME=your-bucket

# Or use local development
PRIMARY_BACKEND=local
LOCAL_STORAGE_PATH=./storage
```

### Check Available Backends

```python
from src.core.storage.manager import BackendRegistry

# List all available backends (with dependencies installed)
print("Available:", BackendRegistry.list_available_backends())

# Check status of all backends
for backend in BackendRegistry.list_all_backends():
    info = BackendRegistry.get_backend_info(backend)
    status = "✅" if info['available'] else "❌"
    print(f"{status} {backend}: {info['status']}")
```

## Supported Backends

| Backend | Status | Use Case | Dependencies |
|---------|--------|----------|--------------|
| **Local** | ✅ Ready | Development | None |
| **MinIO** | ✅ Ready | Staging/Production | aioboto3, boto3 |
| **AWS S3** | ✅ Ready | Production | aioboto3, boto3 |
| **Azure Blob** | ✅ Ready | Enterprise | azure-storage-blob |

## Key Features

- **Zero Code Changes**: Switch backends via configuration only
- **Independent Implementation**: Each backend in its own file
- **Dynamic Loading**: Backends loaded only when needed
- **Graceful Fallback**: Missing dependencies handled elegantly
- **Provider Specialization**: Each backend optimized for its provider

## Architecture Principles

1. **Backend Independence**: No shared code between storage providers
2. **Configuration-Driven**: All switching happens via environment variables
3. **Dependency Isolation**: Each backend manages its own dependencies
4. **Runtime Discovery**: Available backends discovered at startup
5. **Graceful Degradation**: System continues with available backends

---

For detailed technical information, see [BACKENDS.md](./BACKENDS.md).