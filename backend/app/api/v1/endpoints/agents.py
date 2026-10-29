import json
from typing import Optional, List
from fastapi import APIRouter, Depends
from fastapi.responses import StreamingResponse
from pydantic import BaseModel
from sqlalchemy.orm import Session
from app.api import deps
from app.core.database import get_db
from app.models.user import User
from app.models.models import Project

router = APIRouter()

AGENT_SYSTEM_PROMPTS = {
    "planner": (
        "You are a senior software engineering planner. Analyze the given task and project context, "
        "then create a detailed, actionable step-by-step implementation plan with clear milestones. "
        "Be specific about file changes, API design, and integration points."
    ),
    "repository": (
        "You are a repository analysis expert. Analyze the given codebase structure and answer questions "
        "about code organization, file dependencies, architectural patterns, and improvement opportunities. "
        "Provide specific file paths and line references when relevant."
    ),
    "security": (
        "You are a security engineer specializing in code review. Identify security vulnerabilities, "
        "injection risks, authentication flaws, exposed secrets, and OWASP top-10 issues. "
        "For each issue, explain the risk and provide a concrete fix."
    ),
    "architecture": (
        "You are a software architect. Analyze the codebase and provide architectural insights: "
        "design patterns in use, coupling issues, scalability concerns, and recommendations for "
        "improving modularity, testability, and maintainability."
    ),
    "performance": (
        "You are a performance engineering expert. Identify N+1 queries, memory leaks, inefficient "
        "algorithms, missing indexes, unnecessary re-renders, blocking I/O, and CPU bottlenecks. "
        "Provide specific optimizations with expected impact."
    ),
    "testing": (
        "You are a QA and testing expert. Generate comprehensive test cases for the given code: "
        "unit tests, integration tests, edge cases, and error scenarios. "
        "Write actual test code using pytest (Python) or Jest (JavaScript/TypeScript)."
    ),
    "bug_detection": (
        "You are a debugging specialist. Analyze the code for bugs: logic errors, off-by-one errors, "
        "null pointer dereferences, race conditions, incorrect error handling, and type mismatches. "
        "For each bug, explain why it's wrong and provide the corrected code."
    ),
    "documentation": (
        "You are a technical documentation expert. Generate clear, professional documentation: "
        "docstrings, README content, API documentation, architecture diagrams in text, "
        "and inline code comments. Focus on clarity and completeness."
    ),
}


class AgentRunRequest(BaseModel):
    project_id: Optional[str] = None
    task: str
    agent_type: Optional[str] = "planner"
    context: Optional[dict] = None


@router.get("/status")
def get_agents_status(current_user: User = Depends(deps.get_current_user)):
    """Get status of all registered agents."""
    return {
        "agents": [
            {"name": "Planner Agent", "type": "planner", "status": "active",
             "description": "Orchestrates complex multi-step engineering tasks"},
            {"name": "Repository Agent", "type": "repository", "status": "active",
             "description": "Analyzes and navigates codebases with deep understanding"},
            {"name": "Security Agent", "type": "security", "status": "active",
             "description": "Reviews code for vulnerabilities and OWASP top-10 issues"},
            {"name": "Architecture Agent", "type": "architecture", "status": "active",
             "description": "Suggests architectural improvements and design patterns"},
            {"name": "Performance Agent", "type": "performance", "status": "active",
             "description": "Identifies performance bottlenecks and optimizations"},
            {"name": "Testing Agent", "type": "testing", "status": "active",
             "description": "Generates comprehensive test suites and edge cases"},
            {"name": "Bug Detection Agent", "type": "bug_detection", "status": "active",
             "description": "Finds and diagnoses bugs with detailed fix suggestions"},
            {"name": "Documentation Agent", "type": "documentation", "status": "active",
             "description": "Generates professional documentation and docstrings"},
        ],
        "total": 8,
        "active": 8,
    }


@router.post("/run")
async def run_agent(
    payload: AgentRunRequest,
    current_user: User = Depends(deps.get_current_user),
    db: Session = Depends(get_db),
):
    """Run an agent task — returns non-streaming JSON result."""
    from app.services.platform_engine import stream_chat_completion, repository_memory

    agent_type = payload.agent_type or "planner"
    system_prompt = AGENT_SYSTEM_PROMPTS.get(agent_type, AGENT_SYSTEM_PROMPTS["planner"])

    # Build context from project repo if available
    context_block = ""
    if payload.project_id:
        project = db.query(Project).filter(
            Project.id == payload.project_id,
            Project.owner_id == current_user.id
        ).first()
        if project:
            repo_path = str(getattr(project, "repo_path", "") or "")
            if repo_path:
                memory = repository_memory(repo_path)
                context_block = f"\n\nREPOSITORY CONTEXT:\n{memory.get('context_summary', '')}"

    messages = [
        {"role": "system", "content": system_prompt},
        {"role": "user", "content": f"{payload.task}{context_block}"},
    ]

    accumulated = ""
    async for chunk in stream_chat_completion(messages, task_type=agent_type):
        accumulated += chunk.get("content", "")

    return {
        "status": "completed",
        "agent_type": agent_type,
        "task": payload.task,
        "result": accumulated,
        "message": accumulated,
    }


@router.post("/run/stream")
async def run_agent_stream(
    payload: AgentRunRequest,
    current_user: User = Depends(deps.get_current_user),
    db: Session = Depends(get_db),
):
    """Run an agent task with SSE streaming output."""
    from app.services.platform_engine import stream_chat_completion, repository_memory

    agent_type = payload.agent_type or "planner"
    system_prompt = AGENT_SYSTEM_PROMPTS.get(agent_type, AGENT_SYSTEM_PROMPTS["planner"])

    context_block = ""
    if payload.project_id:
        project = db.query(Project).filter(
            Project.id == payload.project_id,
            Project.owner_id == current_user.id
        ).first()
        if project:
            repo_path = str(getattr(project, "repo_path", "") or "")
            if repo_path:
                memory = repository_memory(repo_path)
                context_block = f"\n\nREPOSITORY CONTEXT:\n{memory.get('context_summary', '')}"

    messages = [
        {"role": "system", "content": system_prompt},
        {"role": "user", "content": f"{payload.task}{context_block}"},
    ]

    async def event_stream():
        try:
            async for chunk in stream_chat_completion(messages, task_type=agent_type):
                content = chunk.get("content", "")
                if content:
                    yield f"data: {json.dumps({'content': content, 'agent_type': agent_type, 'provider': chunk.get('provider'), 'model': chunk.get('model')})}\n\n"
                elif chunk.get("done"):
                    yield f"data: {json.dumps({'done': True, 'agent_type': agent_type, 'provider': chunk.get('provider'), 'model': chunk.get('model'), 'latency_ms': chunk.get('latency_ms', 0)})}\n\n"
        except Exception as e:
            yield f"data: {json.dumps({'error': str(e)})}\n\n"
        finally:
            yield "data: [DONE]\n\n"

    return StreamingResponse(event_stream(), media_type="text/event-stream")
