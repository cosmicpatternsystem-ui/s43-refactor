0


def select_current(data: dict) -> dict:
    """MCP-03 compliant resolver. Strict validation — no legacy fallbacks permitted."""
    phases = data.get("phases")
    if not isinstance(phases, list):
        return {
            "status": "INSUFFICIENT_DATA",
            "selection_reason": "phases_not_list",
            "message": "Missing or invalid phases array.",
        }
    for phase in phases:
        if not isinstance(phase, dict):
            continue
        if phase.get("status") in ("complete", "done"):
            continue
        # MCP-03 gate: 'tasks' key must exist and be a list — no 'entries' fallback
        if "tasks" not in phase:
            return {
                "status": "INSUFFICIENT_DATA",
                "selection_reason": "tasks_key_invalid",
                "message": f"Phase '{phase.get('id', '?')}' missing required 'tasks' key.",
            }
        tasks = phase["tasks"]
        if not isinstance(tasks, list):
            return {
                "status": "INSUFFICIENT_DATA",
                "selection_reason": "tasks_key_invalid",
                "message": f"Phase '{phase.get('id', '?')}' 'tasks' must be a list, got {type(tasks).__name__}.",
            }
        for task in tasks:
            if not isinstance(task, dict):
                continue
            if task.get("status", "") in ("complete", "done"):
                continue
            deps = [d for d in task.get("depends_on", []) if d not in {
                t.get("id") for t in tasks if t.get("status") in ("complete", "done")
            }]
            if deps:
                return {
                    "status": "BLOCKED",
                    "current_phase": phase.get("id"),
                    "current_task": task.get("id") or task.get("title"),
                    "blocked_by": deps,
                    "selection_reason": "task_dependencies_unresolved",
                }
            return {
                "status": "READY",
                "current_phase": phase.get("id"),
                "current_task": task.get("id") or task.get("title"),
                "blocked_by": [],
                "selection_reason": "next_open_task",
            }
        return {
            "status": "PHASE_EMPTY_OR_DONE",
            "current_phase": phase.get("id"),
            "selection_reason": "all_tasks_done",
        }
    return {
        "status": "COMPLETE",
        "selection_reason": "no_remaining_phases",
    }
