"""File system service: sandboxed file operations for agents.

Agents can read/write/list files within their project workspace.
All paths are sandboxed to prevent escape from the project directory.
"""

import os
import shutil
from pathlib import Path

from loguru import logger

from app.config import settings
from app.core.exceptions import AuthorizationError, NotFoundError, ValidationError


class FileService:
    """Sandboxed file operations within a project workspace."""

    def __init__(self, project_id: str):
        self.project_id = project_id
        self.workspace = Path(settings.workspace_root) / project_id
        self.workspace.mkdir(parents=True, exist_ok=True)

    def _resolve_safe(self, relative_path: str) -> Path:
        """Resolve a relative path within the workspace, preventing directory traversal."""
        # Normalize and resolve
        clean = relative_path.lstrip("/").replace("\\", "/")
        resolved = (self.workspace / clean).resolve()

        # Ensure it's within workspace
        if not str(resolved).startswith(str(self.workspace.resolve())):
            raise AuthorizationError(detail="路径越界: 不允许访问工作区外的文件")

        return resolved

    def read_file(self, relative_path: str) -> str:
        """Read a file from the project workspace."""
        path = self._resolve_safe(relative_path)
        if not path.exists():
            raise NotFoundError("File", detail=f"文件不存在: {relative_path}")
        if not path.is_file():
            raise ValidationError(detail=f"不是文件: {relative_path}")
        if path.stat().st_size > 1024 * 1024:  # 1MB limit
            raise ValidationError(detail="文件过大 (>1MB)，请分块读取")

        return path.read_text(encoding="utf-8", errors="replace")

    def write_file(self, relative_path: str, content: str) -> dict:
        """Write content to a file in the project workspace."""
        path = self._resolve_safe(relative_path)

        # Create parent directories
        path.parent.mkdir(parents=True, exist_ok=True)

        # Write file
        path.write_text(content, encoding="utf-8")

        logger.info(f"File written: {relative_path} ({len(content)} chars)")
        return {
            "path": relative_path,
            "size": len(content),
            "created": not path.exists(),
        }

    def list_files(self, relative_path: str = "", recursive: bool = False) -> list[dict]:
        """List files in a directory within the workspace."""
        path = self._resolve_safe(relative_path)
        if not path.exists():
            raise NotFoundError("Directory", detail=f"目录不存在: {relative_path}")
        if not path.is_dir():
            raise ValidationError(detail=f"不是目录: {relative_path}")

        items = []
        if recursive:
            for item in sorted(path.rglob("*")):
                if item.name.startswith("."):
                    continue
                rel = str(item.relative_to(self.workspace))
                items.append({
                    "path": rel,
                    "type": "file" if item.is_file() else "dir",
                    "size": item.stat().st_size if item.is_file() else 0,
                })
        else:
            for item in sorted(path.iterdir()):
                if item.name.startswith("."):
                    continue
                rel = str(item.relative_to(self.workspace))
                items.append({
                    "path": rel,
                    "type": "file" if item.is_file() else "dir",
                    "size": item.stat().st_size if item.is_file() else 0,
                })

        return items

    def delete_file(self, relative_path: str) -> None:
        """Delete a file from the workspace."""
        path = self._resolve_safe(relative_path)
        if not path.exists():
            raise NotFoundError("File", detail=f"文件不存在: {relative_path}")
        if path.is_dir():
            shutil.rmtree(path)
        else:
            path.unlink()
        logger.info(f"File deleted: {relative_path}")

    def mkdir(self, relative_path: str) -> None:
        """Create a directory in the workspace."""
        path = self._resolve_safe(relative_path)
        path.mkdir(parents=True, exist_ok=True)

    def get_tree(self, max_depth: int = 3) -> str:
        """Get a tree representation of the workspace."""
        lines = [f"📁 {self.project_id}/"]
        self._build_tree(self.workspace, lines, prefix="", depth=0, max_depth=max_depth)
        return "\n".join(lines)

    def _build_tree(
        self, path: Path, lines: list, prefix: str, depth: int, max_depth: int
    ) -> None:
        if depth >= max_depth:
            return
        items = sorted(
            [i for i in path.iterdir() if not i.name.startswith(".")],
            key=lambda x: (x.is_file(), x.name),
        )
        for i, item in enumerate(items):
            is_last = i == len(items) - 1
            connector = "└── " if is_last else "├── "
            icon = "📄" if item.is_file() else "📁"
            lines.append(f"{prefix}{connector}{icon} {item.name}")
            if item.is_dir():
                extension = "    " if is_last else "│   "
                self._build_tree(item, lines, prefix + extension, depth + 1, max_depth)
