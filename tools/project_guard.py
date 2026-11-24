#!/usr/bin/env python3
"""Project ledger initializer, editor, and deterministic validator."""

from __future__ import annotations

import argparse
import json
import re
import shutil
import sys
from dataclasses import dataclass
from datetime import date
from pathlib import Path
from typing import Dict, Iterable, List, Optional, Tuple

REQUIRED_FILES = (
    "AGENTS.md",
    "PROJECT_RULES.md",
    "PROJECT_STATE.md",
    "TODO.md",
    "DECISIONS.md",
)

ALLOWED_STATUSES = {
    "待处理",
    "进行中",
    "阻塞",
    "待验收",
    "已完成",
    "已废弃",
    "已被替代",
}
ALLOWED_PRIORITIES = {"P0", "P1", "P2", "P3"}
CLOSED_STATUSES = {"已完成", "已废弃", "已被替代"}
TASK_FIELDS = (
    "状态",
    "阶段",
    "优先级",
    "验收条件",
    "依赖",
    "替代关系",
    "执行证据",
    "变更说明",
    "最后更新",
)
STATE_FIELDS = (
    "项目名称",
    "项目目标",
    "当前阶段",
    "当前焦点",
    "阻塞事项",
    "下一步",
    "最后更新",
)
TASK_HEADING = re.compile(r"^##\s+(T-\d{3,})\s*\|\s*(.+?)\s*$", re.MULTILINE)
FIELD_LINE = re.compile(r"^-\s*([^：\n]+)：\s*(.*?)\s*$", re.MULTILINE)
TASK_ID = re.compile(r"T-\d{3,}")
ISO_DATE = re.compile(r"^\d{4}-\d{2}-\d{2}$")
PLACEHOLDERS = {"", "待补充", "待填写", "todo", "tbd", "n/a", "暂无", "无证据"}


@dataclass
class Task:
    task_id: str
    title: str
    fields: Dict[str, str]
    start: int
    end: int


@dataclass
class Issue:
    level: str
    code: str
    message: str

    def as_dict(self) -> Dict[str, str]:
        return {"level": self.level, "code": self.code, "message": self.message}


def today() -> str:
    return date.today().isoformat()


def read_text(path: Path) -> str:
    return path.read_text(encoding="utf-8")


def write_text(path: Path, content: str) -> None:
    path.write_text(content, encoding="utf-8")


def parse_fields(text: str) -> Dict[str, str]:
    return {match.group(1).strip(): match.group(2).strip() for match in FIELD_LINE.finditer(text)}


def parse_tasks(text: str) -> List[Task]:
    matches = list(TASK_HEADING.finditer(text))
    tasks: List[Task] = []
    for index, match in enumerate(matches):
        end = matches[index + 1].start() if index + 1 < len(matches) else len(text)
        block = text[match.end():end]
        tasks.append(
            Task(
                task_id=match.group(1),
                title=match.group(2).strip(),
                fields=parse_fields(block),
                start=match.start(),
                end=end,
            )
        )
    return tasks


def is_placeholder(value: str, allow_none: bool = False) -> bool:
    normalized = value.strip().lower()
    if allow_none and normalized == "无":
        return False
    return normalized in PLACEHOLDERS or normalized.startswith("{{")


def ids_from(value: str) -> List[str]:
    return TASK_ID.findall(value)


def validate_project(project: Path) -> List[Issue]:
    issues: List[Issue] = []
    for name in REQUIRED_FILES:
        path = project / name
        if not path.is_file():
            issues.append(Issue("error", "missing_file", f"缺少必需文件：{name}"))
        elif not read_text(path).strip():
            issues.append(Issue("error", "empty_file", f"文件为空：{name}"))

    if any(issue.code in {"missing_file", "empty_file"} for issue in issues):
        return issues

    state_text = read_text(project / "PROJECT_STATE.md")
    state = parse_fields(state_text)
    for field in STATE_FIELDS:
        if field not in state:
            issues.append(Issue("error", "missing_state_field", f"PROJECT_STATE.md 缺少字段：{field}"))
        elif is_placeholder(state[field], allow_none=field in {"当前焦点", "阻塞事项"}):
            issues.append(Issue("error", "placeholder_state", f"PROJECT_STATE.md 字段尚未填写：{field}"))
    if "最后更新" in state and not ISO_DATE.fullmatch(state["最后更新"]):
        issues.append(Issue("error", "invalid_state_date", "PROJECT_STATE.md 的最后更新必须为 YYYY-MM-DD"))

    todo_text = read_text(project / "TODO.md")
    tasks = parse_tasks(todo_text)
    task_map: Dict[str, Task] = {}
    for task in tasks:
        if task.task_id in task_map:
            issues.append(Issue("error", "duplicate_id", f"待办编号重复：{task.task_id}"))
        task_map[task.task_id] = task

    for task in tasks:
        prefix = task.task_id
        for field in TASK_FIELDS:
            if field not in task.fields:
                issues.append(Issue("error", "missing_task_field", f"{prefix} 缺少字段：{field}"))

        status = task.fields.get("状态", "")
        priority = task.fields.get("优先级", "")
        if status and status not in ALLOWED_STATUSES:
            issues.append(Issue("error", "invalid_status", f"{prefix} 状态不合法：{status}"))
        if priority and priority not in ALLOWED_PRIORITIES:
            issues.append(Issue("error", "invalid_priority", f"{prefix} 优先级不合法：{priority}"))

        for field in ("阶段", "验收条件"):
            if field in task.fields and is_placeholder(task.fields[field]):
                issues.append(Issue("error", "placeholder_task", f"{prefix} 字段尚未填写：{field}"))
        updated = task.fields.get("最后更新", "")
        if updated and not ISO_DATE.fullmatch(updated):
            issues.append(Issue("error", "invalid_task_date", f"{prefix} 最后更新必须为 YYYY-MM-DD"))

        dependencies = ids_from(task.fields.get("依赖", ""))
        replacements = ids_from(task.fields.get("替代关系", ""))
        for relation, related_ids in (("依赖", dependencies), ("替代关系", replacements)):
            for related_id in related_ids:
                if related_id == task.task_id:
                    issues.append(Issue("error", "self_reference", f"{prefix} 的{relation}不能引用自身"))
                elif related_id not in task_map:
                    issues.append(Issue("error", "unknown_reference", f"{prefix} 的{relation}引用不存在的 {related_id}"))

        evidence = task.fields.get("执行证据", "")
        change = task.fields.get("变更说明", "")
        replacement = task.fields.get("替代关系", "")
        if status == "已完成" and is_placeholder(evidence):
            issues.append(Issue("error", "missing_evidence", f"{prefix} 已完成，但没有可复核执行证据"))
        if status == "已废弃" and is_placeholder(change):
            issues.append(Issue("error", "missing_change_reason", f"{prefix} 已废弃，但没有变更原因"))
        if status == "已被替代":
            if is_placeholder(change):
                issues.append(Issue("error", "missing_change_reason", f"{prefix} 已被替代，但没有变更原因"))
            if is_placeholder(replacement) or not replacements:
                issues.append(Issue("error", "missing_replacement", f"{prefix} 已被替代，但没有有效替代项"))

    focus = state.get("当前焦点", "")
    if focus and focus != "无":
        focus_ids = ids_from(focus)
        if not focus_ids:
            issues.append(Issue("error", "invalid_focus", "当前焦点必须为 TODO 编号或“无”"))
        for focus_id in focus_ids:
            if focus_id not in task_map:
                issues.append(Issue("error", "unknown_focus", f"当前焦点引用不存在的 {focus_id}"))
            elif task_map[focus_id].fields.get("状态") in CLOSED_STATUSES:
                issues.append(Issue("error", "closed_focus", f"当前焦点 {focus_id} 已关闭，请更新项目状态"))

    blocking_ids = {
        task.task_id for task in tasks if task.fields.get("状态") == "阻塞"
    }
    state_blockers = state.get("阻塞事项", "")
    if blocking_ids and state_blockers == "无":
        issues.append(Issue("error", "unsynced_blockers", "存在阻塞 TODO，但 PROJECT_STATE.md 仍写“阻塞事项：无”"))
    if not blocking_ids and state_blockers not in {"", "无"}:
        mentioned = set(ids_from(state_blockers))
        unknown = mentioned - set(task_map)
        for task_id in sorted(unknown):
            issues.append(Issue("error", "unknown_blocker", f"阻塞事项引用不存在的 {task_id}"))
        if mentioned and not (mentioned & blocking_ids):
            issues.append(Issue("warning", "stale_blockers", "PROJECT_STATE.md 记录了阻塞编号，但 TODO 中没有阻塞状态"))

    if not tasks:
        issues.append(Issue("warning", "no_tasks", "当前没有 TODO；纯初始化项目可忽略"))
    return issues


def render_task(task_id: str, title: str, status: str, stage: str, priority: str,
                acceptance: str, dependency: str, replacement: str = "无",
                evidence: str = "待补充", change: str = "首次登记") -> str:
    return (
        f"## {task_id} | {title}\n\n"
        f"- 状态：{status}\n"
        f"- 阶段：{stage}\n"
        f"- 优先级：{priority}\n"
        f"- 验收条件：{acceptance}\n"
        f"- 依赖：{dependency}\n"
        f"- 替代关系：{replacement}\n"
        f"- 执行证据：{evidence}\n"
        f"- 变更说明：{change}\n"
        f"- 最后更新：{today()}\n"
    )


def add_task(project: Path, title: str, stage: str, priority: str,
             acceptance: str, dependency: str, status: str) -> str:
    if status not in ALLOWED_STATUSES:
        raise ValueError(f"不合法状态：{status}")
    if priority not in ALLOWED_PRIORITIES:
        raise ValueError(f"不合法优先级：{priority}")
    todo_path = project / "TODO.md"
    if not todo_path.is_file():
        raise ValueError("缺少 TODO.md，请先运行 init")
    text = read_text(todo_path)
    tasks = parse_tasks(text)
    next_number = max((int(t.task_id.split("-")[1]) for t in tasks), default=0) + 1
    task_id = f"T-{next_number:03d}"
    block = render_task(task_id, title.strip(), status, stage.strip(), priority,
                        acceptance.strip(), dependency.strip())
    marker = "<!-- 待办由守门器追加到此处 -->"
    if marker in text:
        text = text.replace(marker, f"{block}\n{marker}", 1)
    else:
        text = text.rstrip() + "\n\n" + block
    write_text(todo_path, text)
    return task_id


def replace_field(block: str, field: str, value: str) -> str:
    pattern = re.compile(rf"^-\s*{re.escape(field)}：.*$", re.MULTILINE)
    replacement = f"- {field}：{value}"
    if pattern.search(block):
        return pattern.sub(replacement, block, count=1)
    return block.rstrip() + "\n" + replacement + "\n"


def transition_task(project: Path, task_id: str, status: str, reason: str,
                    evidence: Optional[str], replacement: Optional[str]) -> None:
    if status not in ALLOWED_STATUSES:
        raise ValueError(f"不合法状态：{status}")
    todo_path = project / "TODO.md"
    text = read_text(todo_path)
    tasks = parse_tasks(text)
    target = next((task for task in tasks if task.task_id == task_id), None)
    if target is None:
        raise ValueError(f"找不到待办：{task_id}")
    if status == "已完成" and (not evidence or is_placeholder(evidence)):
        raise ValueError("标记已完成时必须提供 --evidence")
    if status == "已被替代" and (not replacement or not TASK_ID.fullmatch(replacement)):
        raise ValueError("标记已被替代时必须提供 --replacement T-xxx")
    if replacement and replacement not in {task.task_id for task in tasks}:
        raise ValueError(f"替代项不存在：{replacement}")

    block = text[target.start:target.end]
    block = replace_field(block, "状态", status)
    block = replace_field(block, "变更说明", f"{today()}：{reason.strip()}")
    block = replace_field(block, "最后更新", today())
    if evidence:
        block = replace_field(block, "执行证据", evidence.strip())
    if replacement:
        block = replace_field(block, "替代关系", replacement)
    new_text = text[:target.start] + block + text[target.end:]
    write_text(todo_path, new_text)


def initialize_project(target: Path, name: str, goal: str) -> List[Path]:
    source_root = Path(__file__).resolve().parent.parent
    template_dir = source_root / "templates"
    if not template_dir.is_dir():
        template_dir = source_root / "assets" / "templates"
    if not template_dir.is_dir():
        raise ValueError(f"找不到模板目录：{source_root}")
    target.mkdir(parents=True, exist_ok=True)
    destinations = [target / name_ for name_ in REQUIRED_FILES]
    destinations.append(target / "tools" / "project_guard.py")
    existing = [path for path in destinations if path.exists()]
    if existing:
        joined = ", ".join(str(path) for path in existing)
        raise ValueError(f"为避免覆盖现有文件，初始化已停止；已存在：{joined}")

    created: List[Path] = []
    replacements = {
        "{{PROJECT_NAME}}": name.strip(),
        "{{PROJECT_GOAL}}": goal.strip(),
        "{{TODAY}}": today(),
    }
    for filename in REQUIRED_FILES:
        content = read_text(template_dir / filename)
        for old, new in replacements.items():
            content = content.replace(old, new)
        destination = target / filename
        write_text(destination, content)
        created.append(destination)
    tools_dir = target / "tools"
    tools_dir.mkdir(exist_ok=True)
    guard_destination = tools_dir / "project_guard.py"
    shutil.copy2(Path(__file__).resolve(), guard_destination)
    created.append(guard_destination)
    return created


def print_check(project: Path, as_json: bool) -> int:
    issues = validate_project(project)
    errors = [issue for issue in issues if issue.level == "error"]
    if as_json:
        print(json.dumps({
            "project": str(project.resolve()),
            "ok": not errors,
            "issues": [issue.as_dict() for issue in issues],
        }, ensure_ascii=False, indent=2))
    else:
        if not issues:
            print("PASS：项目账本校验通过，未发现问题。")
        else:
            for issue in issues:
                label = "错误" if issue.level == "error" else "警告"
                print(f"[{label}] {issue.code}: {issue.message}")
            print(f"结果：{len(errors)} 个错误，{len(issues) - len(errors)} 个警告。")
    return 1 if errors else 0


def print_summary(project: Path) -> int:
    todo_path = project / "TODO.md"
    if not todo_path.is_file():
        print("缺少 TODO.md", file=sys.stderr)
        return 2
    tasks = parse_tasks(read_text(todo_path))
    counts = {status: 0 for status in ALLOWED_STATUSES}
    for task in tasks:
        status = task.fields.get("状态")
        if status in counts:
            counts[status] += 1
    print("项目待办摘要")
    for status in ("进行中", "阻塞", "待验收", "待处理", "已完成", "已废弃", "已被替代"):
        print(f"- {status}：{counts[status]}")
    open_tasks = [task for task in tasks if task.fields.get("状态") not in CLOSED_STATUSES]
    if open_tasks:
        print("未关闭事项：")
        for task in open_tasks:
            print(f"- {task.task_id} [{task.fields.get('状态', '未知')}] {task.title}")
    else:
        print("未关闭事项：无")
    return 0


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(description="长期项目账本守门器")
    sub = parser.add_subparsers(dest="command", required=True)

    init_parser = sub.add_parser("init", help="初始化一个新项目")
    init_parser.add_argument("project", type=Path)
    init_parser.add_argument("--name", required=True)
    init_parser.add_argument("--goal", required=True)

    check_parser = sub.add_parser("check", help="校验项目账本")
    check_parser.add_argument("project", type=Path)
    check_parser.add_argument("--json", action="store_true")

    add_parser = sub.add_parser("add", help="新增 TODO")
    add_parser.add_argument("project", type=Path)
    add_parser.add_argument("title")
    add_parser.add_argument("--stage", required=True)
    add_parser.add_argument("--priority", choices=sorted(ALLOWED_PRIORITIES), default="P2")
    add_parser.add_argument("--acceptance", required=True)
    add_parser.add_argument("--dependency", default="无")
    add_parser.add_argument("--status", choices=sorted(ALLOWED_STATUSES), default="待处理")

    transition_parser = sub.add_parser("transition", help="变更 TODO 状态")
    transition_parser.add_argument("project", type=Path)
    transition_parser.add_argument("task_id")
    transition_parser.add_argument("--status", required=True, choices=sorted(ALLOWED_STATUSES))
    transition_parser.add_argument("--reason", required=True)
    transition_parser.add_argument("--evidence")
    transition_parser.add_argument("--replacement")

    summary_parser = sub.add_parser("summary", help="输出当前待办摘要")
    summary_parser.add_argument("project", type=Path)
    return parser


def main(argv: Optional[Iterable[str]] = None) -> int:
    args = build_parser().parse_args(argv)
    try:
        if args.command == "init":
            created = initialize_project(args.project, args.name, args.goal)
            print("初始化完成：")
            for path in created:
                print(f"- {path}")
            return print_check(args.project, as_json=False)
        if args.command == "check":
            return print_check(args.project, args.json)
        if args.command == "add":
            task_id = add_task(args.project, args.title, args.stage, args.priority,
                               args.acceptance, args.dependency, args.status)
            print(f"已新增 {task_id}")
            return print_check(args.project, as_json=False)
        if args.command == "transition":
            transition_task(args.project, args.task_id, args.status, args.reason,
                            args.evidence, args.replacement)
            print(f"已更新 {args.task_id} → {args.status}")
            return print_check(args.project, as_json=False)
        if args.command == "summary":
            return print_summary(args.project)
    except (OSError, ValueError) as exc:
        print(f"ERROR：{exc}", file=sys.stderr)
        return 2
    return 2


if __name__ == "__main__":
    raise SystemExit(main())
