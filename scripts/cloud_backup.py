"""
Nebula Search Engine — Cloud Backup Configuration.
Supports AWS S3 and Azure Blob Storage.

Usage:
    # Configure via environment variables:
    export BACKUP_PROVIDER=s3  # or "azure"
    export AWS_ACCESS_KEY_ID=...
    export AWS_SECRET_ACCESS_KEY=...
    export S3_BUCKET=nebula-backups
    export S3_REGION=us-east-1
    
    # Or for Azure:
    export AZURE_STORAGE_CONNECTION_STRING=...
    export AZURE_CONTAINER=nebula-backups
    
    # Run backup:
    python scripts/cloud_backup.py --backup
    python scripts/cloud_backup.py --restore backup_20260720_120000.tar.gz
    python scripts/cloud_backup.py --list
"""

import argparse
import asyncio
import json
import os
import subprocess
import sys
import tarfile
import tempfile
import time
from datetime import datetime, timezone
from pathlib import Path
from typing import List, Optional


BACKUP_PROVIDER = os.environ.get("BACKUP_PROVIDER", "s3").lower()
S3_BUCKET = os.environ.get("S3_BUCKET", "nebula-backups")
S3_REGION = os.environ.get("S3_REGION", "us-east-1")
AZURE_CONTAINER = os.environ.get("AZURE_CONTAINER", "nebula-backups")
RETENTION_DAYS = int(os.environ.get("BACKUP_RETENTION_DAYS", "30"))
REPO_ROOT = Path(__file__).resolve().parent.parent


def log(msg: str):
    """Log with timestamp."""
    ts = datetime.now(timezone.utc).isoformat()
    print(f"[{ts}] {msg}")


def run_cmd(cmd: List[str], check: bool = True) -> subprocess.CompletedProcess:
    """Run a shell command."""
    log(f"Running: {' '.join(cmd)}")
    result = subprocess.run(cmd, capture_output=True, text=True)
    if check and result.returncode != 0:
        log(f"Command failed: {result.stderr}")
        raise RuntimeError(f"Command failed: {result.stderr}")
    if result.stdout:
        log(f"Output: {result.stdout[:500]}")
    return result


async def create_local_backup() -> Path:
    """Create a local backup archive."""
    timestamp = datetime.now(timezone.utc).strftime("%Y%m%d_%H%M%S")
    backup_name = f"nebula_backup_{timestamp}.tar.gz"
    backup_path = REPO_ROOT / "storage" / "backups" / backup_name
    
    # Ensure backup directory exists
    backup_path.parent.mkdir(parents=True, exist_ok=True)
    
    # Collect paths to backup
    paths_to_backup = [
        REPO_ROOT / "storage" / "uploads",
        REPO_ROOT / "storage" / "vector",
        REPO_ROOT / "storage" / "indexes",
        REPO_ROOT / "storage" / "exports",
    ]
    
    # Add database file if using SQLite
    db_path = REPO_ROOT / "backend" / "nebula.db"
    if db_path.exists():
        paths_to_backup.append(db_path)
    
    # Create tar.gz archive
    log(f"Creating backup archive: {backup_path}")
    with tarfile.open(backup_path, "w:gz") as tar:
        for path in paths_to_backup:
            if path.exists():
                tar.add(path, arcname=path.relative_to(REPO_ROOT))
                log(f"  Added: {path.relative_to(REPO_ROOT)}")
    
    # Create metadata file
    metadata = {
        "timestamp": timestamp,
        "version": "1.1.0",
        "paths": [str(p.relative_to(REPO_ROOT)) for p in paths_to_backup if p.exists()],
        "size_bytes": backup_path.stat().st_size,
    }
    meta_path = backup_path.with_suffix(".json")
    meta_path.write_text(json.dumps(metadata, indent=2))
    
    log(f"Backup created: {backup_path} ({backup_path.stat().st_size / 1024 / 1024:.2f} MB)")
    return backup_path


async def upload_to_s3(local_path: Path) -> bool:
    """Upload backup to AWS S3."""
    try:
        import boto3
        from botocore.exceptions import ClientError
    except ImportError:
        log("boto3 not installed. Install with: pip install boto3")
        return False
    
    try:
        s3 = boto3.client("s3", region_name=S3_REGION)
        key = f"backups/{local_path.name}"
        
        log(f"Uploading to S3: s3://{S3_BUCKET}/{key}")
        s3.upload_file(str(local_path), S3_BUCKET, key)
        
        # Also upload metadata
        meta_path = local_path.with_suffix(".json")
        if meta_path.exists():
            s3.upload_file(str(meta_path), S3_BUCKET, f"backups/{meta_path.name}")
        
        log("S3 upload complete")
        return True
    except ClientError as e:
        log(f"S3 upload failed: {e}")
        return False


async def upload_to_azure(local_path: Path) -> bool:
    """Upload backup to Azure Blob Storage."""
    try:
        from azure.storage.blob import BlobServiceClient
    except ImportError:
        log("azure-storage-blob not installed. Install with: pip install azure-storage-blob")
        return False
    
    conn_string = os.environ.get("AZURE_STORAGE_CONNECTION_STRING", "")
    if not conn_string:
        log("AZURE_STORAGE_CONNECTION_STRING not set")
        return False
    
    try:
        service = BlobServiceClient.from_connection_string(conn_string)
        container = service.get_container_client(AZURE_CONTAINER)
        
        # Ensure container exists
        try:
            container.create_container()
        except Exception:
            pass  # Container may already exist
        
        blob_name = f"backups/{local_path.name}"
        log(f"Uploading to Azure: {AZURE_CONTAINER}/{blob_name}")
        
        with open(local_path, "rb") as data:
            container.upload_blob(name=blob_name, data=data, overwrite=True)
        
        log("Azure upload complete")
        return True
    except Exception as e:
        log(f"Azure upload failed: {e}")
        return False


async def upload_backup(local_path: Path) -> bool:
    """Upload backup to configured cloud provider."""
    if BACKUP_PROVIDER == "s3":
        return await upload_to_s3(local_path)
    elif BACKUP_PROVIDER == "azure":
        return await upload_to_azure(local_path)
    else:
        log(f"Unknown backup provider: {BACKUP_PROVIDER}")
        return False


async def list_backups() -> List[dict]:
    """List available backups."""
    backups = []
    
    # Local backups
    local_dir = REPO_ROOT / "storage" / "backups"
    if local_dir.exists():
        for f in sorted(local_dir.glob("nebula_backup_*.tar.gz"), reverse=True):
            meta_path = f.with_suffix(".json")
            meta = {}
            if meta_path.exists():
                meta = json.loads(meta_path.read_text())
            backups.append({
                "name": f.name,
                "size": f.stat().st_size,
                "modified": datetime.fromtimestamp(f.stat().st_mtime, tz=timezone.utc).isoformat(),
                "location": "local",
                "metadata": meta,
            })
    
    # S3 backups
    if BACKUP_PROVIDER == "s3":
        try:
            import boto3
            s3 = boto3.client("s3", region_name=S3_REGION)
            response = s3.list_objects_v2(Bucket=S3_BUCKET, Prefix="backups/nebula_backup_")
            for obj in response.get("Contents", []):
                if obj["Key"].endswith(".tar.gz"):
                    backups.append({
                        "name": obj["Key"].split("/")[-1],
                        "size": obj["Size"],
                        "modified": obj["LastModified"].isoformat(),
                        "location": f"s3://{S3_BUCKET}/{obj['Key']}",
                    })
        except Exception as e:
            log(f"Failed to list S3 backups: {e}")
    
    return backups


async def restore_backup(backup_name: str) -> bool:
    """Restore from a backup archive."""
    # Find backup file
    local_path = REPO_ROOT / "storage" / "backups" / backup_name
    if not local_path.exists():
        # Try to download from cloud
        log(f"Backup not found locally, attempting cloud download...")
        if BACKUP_PROVIDER == "s3":
            try:
                import boto3
                s3 = boto3.client("s3", region_name=S3_REGION)
                local_path.parent.mkdir(parents=True, exist_ok=True)
                s3.download_file(S3_BUCKET, f"backups/{backup_name}", str(local_path))
                log(f"Downloaded from S3: {local_path}")
            except Exception as e:
                log(f"Failed to download from S3: {e}")
                return False
    
    if not local_path.exists():
        log(f"Backup not found: {backup_name}")
        return False
    
    log(f"Restoring from: {local_path}")
    
    # Create a temporary restore directory
    with tempfile.TemporaryDirectory() as tmpdir:
        tmp_path = Path(tmpdir)
        
        # Extract archive
        with tarfile.open(local_path, "r:gz") as tar:
            tar.extractall(path=tmp_path)
        
        # Restore each path
        for item in tmp_path.iterdir():
            target = REPO_ROOT / item.name
            if target.exists():
                log(f"  Restoring: {item.name} -> {target}")
                # Backup existing
                backup_old = target.parent / f"{target.name}.bak"
                if not backup_old.exists():
                    target.rename(backup_old)
                # Move restored data
                item.rename(target)
    
    log("Restore complete!")
    return True


async def cleanup_old_backups():
    """Remove backups older than retention period."""
    cutoff = time.time() - (RETENTION_DAYS * 86400)
    
    # Local cleanup
    local_dir = REPO_ROOT / "storage" / "backups"
    if local_dir.exists():
        for f in local_dir.glob("nebula_backup_*.tar.gz"):
            if f.stat().st_mtime < cutoff:
                f.unlink()
                log(f"Removed old backup: {f.name}")
                # Also remove metadata
                meta = f.with_suffix(".json")
                if meta.exists():
                    meta.unlink()
    
    # S3 cleanup
    if BACKUP_PROVIDER == "s3":
        try:
            import boto3
            s3 = boto3.client("s3", region_name=S3_REGION)
            response = s3.list_objects_v2(Bucket=S3_BUCKET, Prefix="backups/nebula_backup_")
            for obj in response.get("Contents", []):
                if obj["LastModified"].timestamp() < cutoff:
                    s3.delete_object(Bucket=S3_BUCKET, Key=obj["Key"])
                    log(f"Removed old S3 backup: {obj['Key']}")
        except Exception as e:
            log(f"S3 cleanup failed: {e}")


async def main():
    parser = argparse.ArgumentParser(description="Nebula Search Cloud Backup")
    parser.add_argument("--backup", action="store_true", help="Create a new backup")
    parser.add_argument("--restore", type=str, help="Restore from backup filename")
    parser.add_argument("--list", action="store_true", help="List available backups")
    parser.add_argument("--cleanup", action="store_true", help="Remove old backups")
    parser.add_argument("--upload-only", type=str, help="Upload existing backup file")
    
    args = parser.parse_args()
    
    if args.backup:
        log("Starting backup process...")
        local_path = await create_local_backup()
        uploaded = await upload_backup(local_path)
        if uploaded:
            log("Backup uploaded to cloud successfully")
        else:
            log("Backup saved locally only (cloud upload not configured or failed)")
        await cleanup_old_backups()
    
    elif args.restore:
        log(f"Starting restore from: {args.restore}")
        success = await restore_backup(args.restore)
        if success:
            log("Restore completed successfully")
        else:
            log("Restore failed")
            sys.exit(1)
    
    elif args.list:
        backups = await list_backups()
        if not backups:
            log("No backups found")
        else:
            log(f"Found {len(backups)} backup(s):")
            for b in backups:
                size_mb = b["size"] / 1024 / 1024
                log(f"  {b['name']} ({size_mb:.1f} MB) - {b['modified']} [{b['location']}]")
    
    elif args.cleanup:
        await cleanup_old_backups()
        log("Cleanup complete")
    
    elif args.upload_only:
        path = Path(args.upload_only)
        if not path.exists():
            log(f"File not found: {path}")
            sys.exit(1)
        uploaded = await upload_backup(path)
        if uploaded:
            log("Upload complete")
        else:
            log("Upload failed")
            sys.exit(1)
    
    else:
        parser.print_help()


if __name__ == "__main__":
    asyncio.run(main())