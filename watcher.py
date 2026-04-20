import sys
from typing import Optional

from server_client.application_layer.watcher import Watcher
from server_client.infrastructure_layer.services.project_service import (
    ProjectFileService,
)

if __name__ == "__main__":
    project_file_service = ProjectFileService(file_path="project_file/project_file.sx")

    # If a key is passed, use it; otherwise None
    known_key: Optional[str] = sys.argv[1] if len(sys.argv) > 1 else None

    watcher = Watcher(project_file_service, known_key=known_key)
    watcher.start()
