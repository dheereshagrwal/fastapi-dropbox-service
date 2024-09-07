import os
import uuid
from datetime import datetime, timezone
from fastapi import FastAPI, UploadFile, File, HTTPException
import redis

# Initialize FastAPI app
app = FastAPI(
    title="Dropbox-like Service",
    description="A simplified Dropbox service for file uploads and metadata management.",
    version="1.0.0",
)

# Redis client
redis_client = redis.Redis(host="redis", port=6379, decode_responses=True)

# File storage path inside the Docker container
FILE_STORAGE_PATH = "/files"
os.makedirs(FILE_STORAGE_PATH, exist_ok=True)


# Upload a file
@app.post("/files/upload")
async def upload_file(file: UploadFile = File(...)):
    file_id = str(uuid.uuid4())
    file_path = os.path.join(FILE_STORAGE_PATH, file_id)

    # Write file to disk
    with open(file_path, "wb") as f:
        f.write(await file.read())

    # Save metadata to Redis
    metadata = {
        "filename": file.filename,
        "created_at": datetime.now(timezone.utc).isoformat(),
        "size": file.size,
        "content_type": file.content_type,
    }
    redis_client.hmset(f"file:{file_id}", metadata)

    return {"file_id": file_id, "metadata": metadata}


# Get a file by its file_id
@app.get("/files/{file_id}")
async def get_file(file_id: str):
    file_path = os.path.join(FILE_STORAGE_PATH, file_id)
    if not os.path.exists(file_path):
        raise HTTPException(status_code=404, detail="File not found")

    # Retrieve metadata from Redis
    metadata = redis_client.hgetall(f"file:{file_id}")

    if not metadata:
        raise HTTPException(status_code=404, detail="Metadata not found")

    # Return file data and metadata in the requested format
    return {
        "file_id": file_id,
        "metadata": metadata,
    }


# Delete a file by its file_id
@app.delete("/files/{file_id}")
async def delete_file(file_id: str):
    file_path = os.path.join(FILE_STORAGE_PATH, file_id)

    if os.path.exists(file_path):
        os.remove(file_path)
        redis_client.delete(f"file:{file_id}")
        return {"message": "File deleted"}

    raise HTTPException(status_code=404, detail="File not found")


# List all files
@app.get("/files")
async def list_files():
    file_keys = redis_client.keys("file:*")
    files = [None] * len(file_keys)

    for i, key in enumerate(file_keys):
        file_id = key.split(":")[1]  # Extract file_id from Redis key
        metadata = redis_client.hgetall(key)
        files[i] = {"file_id": file_id, "metadata": metadata}

    return files
