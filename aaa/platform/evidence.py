import hashlib
import json
import base64
from typing import Optional, Any
from datetime import datetime

class EvidenceStore:
    def __init__(self):
        # Mocking storage
        self._objects = {}  # uri -> content
        self._index = []    # list of metadata dicts

    def store_artefact(self, engagement_id: str, phase: str, artefact_type: str, content: Any, agent_name: str) -> str:
        """Stores an artefact and returns its URI."""
        data_str = json.dumps(content)
        sha256 = hashlib.sha256(data_str.encode()).hexdigest()
        uri = f"minio://{engagement_id}/{phase}/{artefact_type}_{sha256[:8]}.json"
        
        self._objects[uri] = content
        
        metadata = {
            "engagement_id": engagement_id,
            "phase": phase,
            "artefact_type": artefact_type,
            "uri": uri,
            "sha256": sha256,
            "created_at": datetime.utcnow().isoformat(),
            "created_by_agent": agent_name
        }
        self._index.append(metadata)
        
        return uri

    def store_file(
        self,
        engagement_id: str,
        phase: str,
        artefact_type: str,
        filename: str,
        content_type: str,
        data: bytes,
        agent_name: str,
    ) -> str:
        """Store binary file bytes and return a MinIO-style URI."""
        sha256 = hashlib.sha256(data).hexdigest()
        safe_name = filename.replace("/", "_").replace("\\", "_") or "upload.bin"
        uri = f"minio://{engagement_id}/{phase}/{artefact_type}_{sha256[:8]}_{safe_name}"
        payload = {
            "filename": filename,
            "content_type": content_type,
            "bytes_size": len(data),
            "sha256": sha256,
            "body_base64": base64.b64encode(data).decode("ascii"),
        }
        self._objects[uri] = payload
        self._index.append({
            "engagement_id": engagement_id,
            "phase": phase,
            "artefact_type": artefact_type,
            "filename": filename,
            "content_type": content_type,
            "bytes_size": len(data),
            "uri": uri,
            "sha256": sha256,
            "created_at": datetime.utcnow().isoformat(),
            "created_by_agent": agent_name,
        })
        return uri

    def get_artefact(self, uri: str) -> Optional[Any]:
        """Retrieves an artefact by its URI."""
        return self._objects.get(uri)

    def get_index(self, engagement_id: str) -> list[dict]:
        """Returns the index entries for a given engagement."""
        return [entry for entry in self._index if entry["engagement_id"] == engagement_id]
