"""Agent tool system: extensible tool registry for agent function calling.

Tools are registered with name, description, and parameters schema.
The LLM decides which tool to call based on the conversation context.
Tools execute in a sandboxed environment with project-scoped permissions.
"""

import asyncio
import json
import subprocess
from abc import ABC, abstractmethod
from dataclasses import dataclass, field
from typing import Any

from loguru import logger


@dataclass
class ToolResult:
    """Result from a tool execution."""

    success: bool
    output: str
    error: str | None = None
    metadata: dict[str, Any] = field(default_factory=dict)


@dataclass
class ToolParam:
    """Tool parameter definition."""

    name: str
    type: str  # "string", "integer", "boolean", "array"
    description: str
    required: bool = True
    default: Any = None


class BaseTool(ABC):
    """Base class for all agent tools."""

    name: str
    description: str
    params: list[ToolParam]

    @abstractmethod
    async def execute(self, project_id: str, **kwargs: Any) -> ToolResult:
        """Execute the tool with given parameters."""
        ...

    def to_schema(self) -> dict:
        """Convert to OpenAI function calling schema."""
        properties = {}
        required = []
        for p in self.params:
            properties[p.name] = {
                "type": p.type,
                "description": p.description,
            }
            if p.required:
                required.append(p.name)

        return {
            "type": "function",
            "function": {
                "name": self.name,
                "description": self.description,
                "parameters": {
                    "type": "object",
                    "properties": properties,
                    "required": required,
                },
            },
        }


class ShellTool(BaseTool):
    """Execute shell commands in a sandboxed environment."""

    name = "shell_exec"
    description = "在项目工作区内执行 shell 命令。用于运行脚本、安装依赖、编译代码等。"
    params = [
        ToolParam(name="command", type="string", description="要执行的 shell 命令"),
        ToolParam(
            name="workdir",
            type="string",
            description="工作目录（相对于项目根目录）",
            required=False,
            default="",
        ),
        ToolParam(
            name="timeout",
            type="integer",
            description="超时时间（秒）",
            required=False,
            default=30,
        ),
    ]

    async def execute(self, project_id: str, **kwargs: Any) -> ToolResult:
        from app.config import settings
        from pathlib import Path

        command = kwargs.get("command", "")
        workdir = kwargs.get("workdir", "")
        timeout = min(kwargs.get("timeout", 30), 60)  # Max 60s

        workspace = Path(settings.workspace_root) / project_id
        workspace.mkdir(parents=True, exist_ok=True)

        if workdir:
            cwd = (workspace / workdir).resolve()
            if not str(cwd).startswith(str(workspace.resolve())):
                return ToolResult(success=False, output="", error="路径越界")
        else:
            cwd = workspace

        # Block dangerous commands
        blocked = ["rm -rf /", "mkfs", "dd if=", ":(){", "fork bomb"]
        if any(b in command for b in blocked):
            return ToolResult(success=False, output="", error="命令被安全策略阻止")

        try:
            proc = await asyncio.create_subprocess_shell(
                command,
                stdout=asyncio.subprocess.PIPE,
                stderr=asyncio.subprocess.PIPE,
                cwd=str(cwd),
                env={"PATH": "/usr/local/bin:/usr/bin:/bin", "HOME": str(workspace)},
            )
            stdout, stderr = await asyncio.wait_for(
                proc.communicate(), timeout=timeout
            )

            output = stdout.decode("utf-8", errors="replace")[:10000]
            err_output = stderr.decode("utf-8", errors="replace")[:5000]

            return ToolResult(
                success=proc.returncode == 0,
                output=output,
                error=err_output if proc.returncode != 0 else None,
                metadata={"exit_code": proc.returncode},
            )

        except asyncio.TimeoutError:
            return ToolResult(success=False, output="", error=f"命令超时 ({timeout}s)")
        except Exception as e:
            return ToolResult(success=False, output="", error=str(e))


class FileReadTool(BaseTool):
    """Read a file from the project workspace."""

    name = "read_file"
    description = "读取项目工作区中的文件内容。"
    params = [
        ToolParam(name="path", type="string", description="文件路径（相对于项目根目录）"),
    ]

    async def execute(self, project_id: str, **kwargs: Any) -> ToolResult:
        from app.services.file_service import FileService

        path = kwargs.get("path", "")
        try:
            fs = FileService(project_id)
            content = fs.read_file(path)
            return ToolResult(
                success=True,
                output=content,
                metadata={"path": path, "size": len(content)},
            )
        except Exception as e:
            return ToolResult(success=False, output="", error=str(e))


class FileWriteTool(BaseTool):
    """Write content to a file in the project workspace."""

    name = "write_file"
    description = "将内容写入项目工作区中的文件。如果文件不存在则创建。"
    params = [
        ToolParam(name="path", type="string", description="文件路径（相对于项目根目录）"),
        ToolParam(name="content", type="string", description="要写入的文件内容"),
    ]

    async def execute(self, project_id: str, **kwargs: Any) -> ToolResult:
        from app.services.file_service import FileService

        path = kwargs.get("path", "")
        content = kwargs.get("content", "")
        try:
            fs = FileService(project_id)
            result = fs.write_file(path, content)
            return ToolResult(
                success=True,
                output=f"文件已写入: {path} ({result['size']} 字符)",
                metadata=result,
            )
        except Exception as e:
            return ToolResult(success=False, output="", error=str(e))


class ListFilesTool(BaseTool):
    """List files in the project workspace."""

    name = "list_files"
    description = "列出项目工作区中的文件和目录。"
    params = [
        ToolParam(
            name="path",
            type="string",
            description="目录路径（相对于项目根目录）",
            required=False,
            default="",
        ),
        ToolParam(
            name="recursive",
            type="boolean",
            description="是否递归列出",
            required=False,
            default=False,
        ),
    ]

    async def execute(self, project_id: str, **kwargs: Any) -> ToolResult:
        from app.services.file_service import FileService

        path = kwargs.get("path", "")
        recursive = kwargs.get("recursive", False)
        try:
            fs = FileService(project_id)
            items = fs.list_files(path, recursive=recursive)
            output = "\n".join(
                f"{'📁' if i['type'] == 'dir' else '📄'} {i['path']} ({i['size']}B)"
                for i in items
            )
            return ToolResult(
                success=True,
                output=output or "(空目录)",
                metadata={"count": len(items)},
            )
        except Exception as e:
            return ToolResult(success=False, output="", error=str(e))


class CodeAnalyzeTool(BaseTool):
    """Analyze code structure and quality."""

    name = "analyze_code"
    description = "分析代码文件的结构、复杂度和潜在问题。"
    params = [
        ToolParam(name="path", type="string", description="要分析的文件路径"),
        ToolParam(
            name="analysis_type",
            type="string",
            description="分析类型: structure(结构), issues(问题), summary(摘要)",
            required=False,
            default="summary",
        ),
    ]

    async def execute(self, project_id: str, **kwargs: Any) -> ToolResult:
        from app.services.file_service import FileService

        path = kwargs.get("path", "")
        analysis_type = kwargs.get("analysis_type", "summary")

        try:
            fs = FileService(project_id)
            content = fs.read_file(path)
            lines = content.split("\n")

            if analysis_type == "structure":
                output = self._analyze_structure(path, lines)
            elif analysis_type == "issues":
                output = self._analyze_issues(path, lines)
            else:
                output = self._analyze_summary(path, lines)

            return ToolResult(success=True, output=output)
        except Exception as e:
            return ToolResult(success=False, output="", error=str(e))

    def _analyze_summary(self, path: str, lines: list[str]) -> str:
        ext = path.rsplit(".", 1)[-1] if "." in path else "unknown"
        total_lines = len(lines)
        non_empty = sum(1 for l in lines if l.strip())
        comment_lines = sum(
            1 for l in lines if l.strip().startswith(("#", "//", "/*", "*", "'''", '"""'))
        )
        return (
            f"文件: {path}\n"
            f"语言: {ext}\n"
            f"总行数: {total_lines}\n"
            f"有效行数: {non_empty}\n"
            f"注释行数: {comment_lines}\n"
            f"注释率: {comment_lines / max(non_empty, 1) * 100:.1f}%"
        )

    def _analyze_structure(self, path: str, lines: list[str]) -> str:
        functions = []
        classes = []
        imports = []
        for i, line in enumerate(lines, 1):
            stripped = line.strip()
            if stripped.startswith(("def ", "async def ")):
                name = stripped.split("(")[0].replace("def ", "").replace("async ", "")
                functions.append(f"  L{i}: {name}")
            elif stripped.startswith("class "):
                name = stripped.split("(")[0].split(":")[0].replace("class ", "")
                classes.append(f"  L{i}: {name}")
            elif stripped.startswith(("import ", "from ")):
                imports.append(stripped)

        parts = [f"文件: {path}"]
        if classes:
            parts.append(f"\n类 ({len(classes)}):\n" + "\n".join(classes))
        if functions:
            parts.append(f"\n函数 ({len(functions)}):\n" + "\n".join(functions))
        if imports:
            parts.append(f"\n导入 ({len(imports)}): {', '.join(imports[:10])}")
        return "\n".join(parts)

    def _analyze_issues(self, path: str, lines: list[str]) -> str:
        issues = []
        for i, line in enumerate(lines, 1):
            if len(line) > 120:
                issues.append(f"  L{i}: 行过长 ({len(line)} 字符)")
            if "TODO" in line or "FIXME" in line or "HACK" in line:
                issues.append(f"  L{i}: {line.strip()[:80]}")
            if "pass" == line.strip() and i > 1:
                issues.append(f"  L{i}: 空实现 (pass)")

        long_funcs = []
        func_start = None
        for i, line in enumerate(lines, 1):
            if line.strip().startswith(("def ", "async def ")):
                if func_start and (i - func_start) > 50:
                    long_funcs.append(f"  L{func_start}: 函数过长 ({i - func_start} 行)")
                func_start = i

        all_issues = issues + long_funcs
        if not all_issues:
            return "未发现明显问题 ✓"
        return f"发现 {len(all_issues)} 个潜在问题:\n" + "\n".join(all_issues[:20])


class SearchCodeTool(BaseTool):
    """Search for patterns in project code."""

    name = "search_code"
    description = "在项目代码中搜索关键词或正则表达式。"
    params = [
        ToolParam(name="pattern", type="string", description="搜索模式（支持正则）"),
        ToolParam(
            name="path",
            type="string",
            description="搜索目录（相对于项目根目录）",
            required=False,
            default="",
        ),
        ToolParam(
            name="file_ext",
            type="string",
            description="文件扩展名过滤（如 .py, .ts）",
            required=False,
            default="",
        ),
    ]

    async def execute(self, project_id: str, **kwargs: Any) -> ToolResult:
        import re
        from app.services.file_service import FileService

        pattern = kwargs.get("pattern", "")
        search_path = kwargs.get("path", "")
        file_ext = kwargs.get("file_ext", "")

        try:
            fs = FileService(project_id)
            items = fs.list_files(search_path, recursive=True)
            regex = re.compile(pattern, re.IGNORECASE)

            matches = []
            for item in items:
                if item["type"] != "file":
                    continue
                if file_ext and not item["path"].endswith(file_ext):
                    continue
                try:
                    content = fs.read_file(item["path"])
                    for i, line in enumerate(content.split("\n"), 1):
                        if regex.search(line):
                            matches.append(f"{item['path']}:L{i}: {line.strip()[:100]}")
                            if len(matches) >= 50:
                                break
                except Exception:
                    continue
                if len(matches) >= 50:
                    break

            output = "\n".join(matches) if matches else "未找到匹配"
            return ToolResult(
                success=True,
                output=output,
                metadata={"match_count": len(matches)},
            )
        except Exception as e:
            return ToolResult(success=False, output="", error=str(e))


# --- Tool Registry ---


class ToolRegistry:
    """Registry of available tools for agents."""

    def __init__(self) -> None:
        self._tools: dict[str, BaseTool] = {}

    def register(self, tool: BaseTool) -> None:
        self._tools[tool.name] = tool

    def get(self, name: str) -> BaseTool | None:
        return self._tools.get(name)

    def list_tools(self) -> list[BaseTool]:
        return list(self._tools.values())

    def get_schemas(self) -> list[dict]:
        """Get all tool schemas for LLM function calling."""
        return [tool.to_schema() for tool in self._tools.values()]

    async def execute(self, tool_name: str, project_id: str, **kwargs: Any) -> ToolResult:
        """Execute a tool by name."""
        tool = self._tools.get(tool_name)
        if not tool:
            return ToolResult(success=False, output="", error=f"未知工具: {tool_name}")

        logger.info(f"Tool call: {tool_name} | project={project_id} | args={kwargs}")
        result = await tool.execute(project_id, **kwargs)
        logger.info(f"Tool result: {tool_name} | success={result.success}")
        return result


# Singleton registry with default tools
tool_registry = ToolRegistry()
tool_registry.register(ShellTool())
tool_registry.register(FileReadTool())
tool_registry.register(FileWriteTool())
tool_registry.register(ListFilesTool())
tool_registry.register(CodeAnalyzeTool())
tool_registry.register(SearchCodeTool())
