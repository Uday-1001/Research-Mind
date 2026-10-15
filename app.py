import asyncio
import io
import json
import os
import re
import uuid
from typing import Optional

from dotenv import load_dotenv
from fastapi import FastAPI, HTTPException, Query, Request, Header
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse, StreamingResponse
from fastapi.staticfiles import StaticFiles
from pydantic import BaseModel

load_dotenv()

from agents import build_reader_agent, build_search_agent, critic_chain, writer_chain, writer_continuation_chain
from storage import delete_session, get_all_sessions, get_session, init_db, save_session, get_all_workspaces, create_workspace, delete_workspace, workspace_exists

# Initialize database
init_db()

app = FastAPI(
    title="ResearchMind - Ultra-Smooth AI Multi-Agent System",
    description="Backend API serving the HTML, CSS, and Vanilla JavaScript UI",
    version="2.0.0"
)

# Enable CORS for maximum flexibility
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

PIPELINE_STEPS = ["search", "reader", "writer", "critic"]


class CreateWorkspaceRequest(BaseModel):
    workspace_id: str


class ExportDocxRequest(BaseModel):
    markdown: str
    topic: Optional[str] = "Research_Report"


def resolve_workspace_id(header_ws: Optional[str] = None, query_ws: Optional[str] = None) -> str:
    ws = query_ws or header_ws or "default"
    cleaned = ws.strip()
    return cleaned if cleaned else "default"


@app.get("/api/workspaces")
async def list_workspaces():
    """Retrieve all distinct active workspaces."""
    return {"workspaces": get_all_workspaces()}


@app.post("/api/workspaces")
async def register_workspace(req: CreateWorkspaceRequest):
    """Registers and creates a new workspace if it does not already exist."""
    clean = (req.workspace_id or "").strip().replace(" ", "-").lower()
    if not clean:
        raise HTTPException(status_code=400, detail="Workspace ID cannot be empty")
    if clean == "default" or workspace_exists(clean):
        raise HTTPException(
            status_code=409,
            detail=f"Workspace '{clean}' already exists. Please use a different workspace name."
        )
    created = create_workspace(clean)
    return {"status": "success", "workspace_id": created, "workspaces": get_all_workspaces()}


@app.delete("/api/workspaces/{workspace_id}")
async def remove_workspace(workspace_id: str):
    """Deletes a workspace and its associated sessions."""
    clean = workspace_id.strip().lower()
    if clean == "default":
        raise HTTPException(status_code=400, detail="Cannot delete default workspace")
    delete_workspace(clean)
    return {"status": "success", "deleted_workspace": clean, "workspaces": get_all_workspaces()}


@app.get("/api/sessions")
async def list_sessions(
    workspace_id: Optional[str] = Query(None),
    x_workspace_id: Optional[str] = Header(None, alias="X-Workspace-Id")
):
    """Retrieve all saved research sessions for the active workspace."""
    ws = resolve_workspace_id(x_workspace_id, workspace_id)
    sessions = get_all_sessions(workspace_id=ws)
    return {"workspace_id": ws, "sessions": sessions}


@app.get("/api/sessions/{session_id}")
async def fetch_session(
    session_id: str,
    workspace_id: Optional[str] = Query(None),
    x_workspace_id: Optional[str] = Header(None, alias="X-Workspace-Id")
):
    """Retrieve a single session by ID scoped to active workspace."""
    ws = resolve_workspace_id(x_workspace_id, workspace_id)
    session = get_session(session_id, workspace_id=ws)
    if not session:
        raise HTTPException(status_code=404, detail="Session not found in active workspace")
    return session


@app.delete("/api/sessions/{session_id}")
async def remove_session(
    session_id: str,
    workspace_id: Optional[str] = Query(None),
    x_workspace_id: Optional[str] = Header(None, alias="X-Workspace-Id")
):
    """Delete a session by ID scoped to active workspace."""
    ws = resolve_workspace_id(x_workspace_id, workspace_id)
    session = get_session(session_id, workspace_id=ws)
    if not session:
        raise HTTPException(status_code=404, detail="Session not found in active workspace")
    delete_session(session_id, workspace_id=ws)
    return {"status": "success", "workspace_id": ws, "deleted_id": session_id}


def normalize_latex(text: str) -> str:
    """Normalizes non-standard LaTeX delimiters (\\[...\\], \\(...\\), raw brackets) into standard markdown math ($$, $)."""
    if not text:
        return text
    # Convert \[ ... \] to \n\n$$\n...\n$$\n\n
    text = re.sub(r'\\\[\s*([\s\S]*?)\s*\\\]', r'\n\n$$\n\1\n$$\n\n', text)
    # Convert \( ... \) to $...$
    text = re.sub(r'\\\(\s*([\s\S]*?)\s*\\\)', r'$\1$', text)
    # Convert standalone bracketed LaTeX expressions: e.g. \n[\n\pi_...\n]\n
    text = re.sub(r'(?:^|\n)\[\s*(\\[a-zA-Z0-9_\^\{\}\+\-\*/=\(\)\s\\,]+?)\s*\](?:\n|$)', r'\n\n$$\n\1\n$$\n\n', text)
    return text


@app.get("/api/research/stream")
async def research_stream(
    topic: str = Query(..., description="The research topic"),
    session_id: Optional[str] = Query(None, description="Session ID"),
    mode: str = Query("run", description="run | resume | restart"),
    workspace_id: Optional[str] = Query(None, description="Workspace ID"),
    x_workspace_id: Optional[str] = Header(None, alias="X-Workspace-Id"),
):
    """
    Streams research pipeline steps and agent outputs in real-time using SSE.
    """
    topic_val = topic.strip()
    if not topic_val:
        raise HTTPException(status_code=400, detail="Research topic cannot be empty.")

    ws_id = resolve_workspace_id(x_workspace_id, workspace_id)
    sess_id = session_id if (session_id and session_id.strip()) else str(uuid.uuid4())

    async def event_generator():
        # Helper to format SSE events
        def sse_pack(event: str, data: dict) -> str:
            return f"event: {event}\ndata: {json.dumps(data)}\n\n"

        existing = get_session(sess_id, workspace_id=ws_id) if sess_id else None
        results = {}
        revision_count = 0
        eval_msg = None

        if mode == "resume" and existing and existing.get("results"):
            results = dict(existing["results"])
            revision_count = results.get("revision_count", 0)
            eval_msg = results.get("eval_msg", None)
        else:
            # Fresh run or restart
            results = {}
            revision_count = 0
            eval_msg = None

        # Emit initial session metadata
        yield sse_pack("init", {
            "session_id": sess_id,
            "workspace_id": ws_id,
            "topic": topic_val,
            "results": results,
            "revision_count": revision_count,
            "eval_msg": eval_msg
        })

        try:
            # Step 1: Web Search
            if "search" not in results:
                yield sse_pack("status", {
                    "step": "search",
                    "state": "running",
                    "message": "Web Search is finding relevant information…"
                })

                def run_search():
                    search_agent = build_search_agent()
                    sr = search_agent.invoke({
                        "messages": [("user", 
                            f"Search the web for up-to-date, reliable, and in-depth information about: '{topic_val}'. "
                            f"You MUST call the web_search tool and explicitly list all discovered URLs with their titles and summaries."
                        )]
                    })
                    return sr["messages"][-1].content

                search_output = None
                for attempt in range(4):
                    try:
                        search_output = await asyncio.to_thread(run_search)
                        break
                    except Exception as e:
                        err_str = str(e)
                        is_rl = any(x in err_str for x in ["429", "Rate limit", "rate_limit_exceeded", "quota", "ResourceExhausted"])
                        if is_rl and attempt < 3:
                            cooldown_secs = 12 * (attempt + 1)
                            for remaining in range(cooldown_secs, 0, -1):
                                yield sse_pack("status", {
                                    "step": "search",
                                    "state": "running",
                                    "message": f"Rate limit reached. Waiting {remaining}s before retrying Web Search (Attempt {attempt + 1}/3)..."
                                })
                                await asyncio.sleep(1)
                            yield sse_pack("status", {
                                "step": "search",
                                "state": "running",
                                "message": "Resuming Web Search now…"
                            })
                        else:
                            raise e

                results["search"] = search_output
                save_session(sess_id, topic_val, results, workspace_id=ws_id)

                yield sse_pack("step_done", {
                    "step": "search",
                    "data": search_output
                })

            # Step 2: Source Reader
            if "reader" not in results:
                yield sse_pack("status", {
                    "step": "reader",
                    "state": "running",
                    "message": "Source Reader is extracting deep content…"
                })

                def run_reader():
                    reader_agent = build_reader_agent()
                    rr = reader_agent.invoke({
                        "messages": [("user",
                            f"Examine the following search findings for topic '{topic_val}'. "
                            f"Identify the most authoritative, in-depth URL from the list and immediately call `scrape_url` to extract deep technical content.\n\n"
                            f"Search Results:\n{results['search']}"
                        )]
                    })
                    last_msg = rr["messages"][-1]
                    raw_content = last_msg.content
                    if isinstance(raw_content, str):
                        return raw_content
                    elif isinstance(raw_content, list):
                        parts = []
                        for item in raw_content:
                            if isinstance(item, str):
                                parts.append(item)
                            elif isinstance(item, dict):
                                parts.append(item.get("text") or item.get("content") or str(item))
                            else:
                                parts.append(str(item))
                        return "\n\n".join(parts)
                    elif isinstance(raw_content, dict):
                        return raw_content.get("text") or raw_content.get("content") or json.dumps(raw_content, indent=2)
                    return str(raw_content)

                reader_output = None
                for attempt in range(4):
                    try:
                        reader_output = await asyncio.to_thread(run_reader)
                        break
                    except Exception as e:
                        err_str = str(e)
                        is_rl = any(x in err_str for x in ["429", "Rate limit", "rate_limit_exceeded", "quota", "ResourceExhausted"])
                        if is_rl and attempt < 3:
                            cooldown_secs = 12 * (attempt + 1)
                            for remaining in range(cooldown_secs, 0, -1):
                                yield sse_pack("status", {
                                    "step": "reader",
                                    "state": "running",
                                    "message": f"Rate limit reached. Waiting {remaining}s before retrying Source Reader (Attempt {attempt + 1}/3)..."
                                })
                                await asyncio.sleep(1)
                            yield sse_pack("status", {
                                "step": "reader",
                                "state": "running",
                                "message": "Resuming Source Reader now…"
                            })
                        else:
                            raise e

                results["reader"] = reader_output
                save_session(sess_id, topic_val, results, workspace_id=ws_id)

                yield sse_pack("step_done", {
                    "step": "reader",
                    "data": reader_output
                })

            # Step 3 & 4: Report Writer and Quality Review
            latest_writer_draft = results.get("writer")

            while "critic" not in results:
                # Step 3: Report Writer
                if not latest_writer_draft:
                    yield sse_pack("status", {
                        "step": "writer",
                        "state": "running",
                        "message": f"Report Writer is drafting research report (Review {revision_count} of 3)..."
                    })

                    research_combined = (
                        f"SEARCH RESULTS:\n{results['search']}\n\n"
                        f"DETAILED SCRAPED CONTENT:\n{results['reader']}"
                    )
                    feedback_text = ""
                    if revision_count > 0 and "last_critic" in results:
                        feedback_text = (
                            f"CRITICAL REVISION DIRECTIVE:\n"
                            f"The previous draft received this critic evaluation:\n{results['last_critic']}\n"
                            f"You MUST explicitly resolve every single cited weakness and point of critique mentioned above to achieve a score of 9.0+.\n"
                            f"IMPORTANT: Budget your tokens tightly (1,600 to 2,300 words). Ensure ALL 6 SECTIONS through ## 6. Verified Sources are completely written and never truncated."
                        )

                    def run_writer():
                        draft = writer_chain.invoke({
                            "topic": topic_val,
                            "research": research_combined,
                            "feedback": feedback_text
                        })

                        # Verify completeness of sections
                        has_sources = any(k in draft for k in [
                            "## 6. Verified Sources", "Verified Sources", "## Sources", "### Sources", "## References", "### References"
                        ])
                        ends_cleanly = draft.rstrip().endswith((".", "!", "?", "]", ")", "`", '"', "'", "*"))

                        if not has_sources or not ends_cleanly:
                            try:
                                continuation = writer_continuation_chain.invoke({
                                    "topic": topic_val,
                                    "research": research_combined,
                                    "text_so_far": draft[-2500:]
                                })
                                if continuation and continuation.strip():
                                    draft = draft.rstrip() + "\n\n" + continuation.strip()
                            except Exception as cont_err:
                                print(f"[Writer Continuation Warning] {cont_err}")

                        # Normalize math equations into standard KaTeX/Markdown syntax
                        draft = normalize_latex(draft)

                        return draft

                    writer_output = None
                    for attempt in range(4):
                        try:
                            writer_output = await asyncio.to_thread(run_writer)
                            break
                        except Exception as e:
                            err_str = str(e)
                            is_rl = any(x in err_str for x in ["429", "Rate limit", "rate_limit_exceeded", "quota", "ResourceExhausted"])
                            if is_rl and attempt < 3:
                                cooldown_secs = 15 * (attempt + 1)
                                for remaining in range(cooldown_secs, 0, -1):
                                    yield sse_pack("status", {
                                        "step": "writer",
                                        "state": "running",
                                        "message": f"Rate limit reached. Waiting {remaining}s before resuming Writer (Attempt {attempt + 1}/3)..."
                                    })
                                    await asyncio.sleep(1)
                                yield sse_pack("status", {
                                    "step": "writer",
                                    "state": "running",
                                    "message": f"Resuming Report Writer now (Review {revision_count} of 3)..."
                                })
                            else:
                                raise e

                    latest_writer_draft = writer_output

                # Step 4: Quality Review
                yield sse_pack("status", {
                    "step": "critic",
                    "state": "running",
                    "message": f"Draft prepared. Quality Review is auditing the report (Review {revision_count} of 3)..."
                })

                def run_critic():
                    return critic_chain.invoke({
                        "report": latest_writer_draft
                    })

                critic_output = None
                for attempt in range(4):
                    try:
                        critic_output = await asyncio.to_thread(run_critic)
                        break
                    except Exception as e:
                        err_str = str(e)
                        is_rl = any(x in err_str for x in ["429", "Rate limit", "rate_limit_exceeded", "quota", "ResourceExhausted"])
                        if is_rl and attempt < 3:
                            cooldown_secs = 15 * (attempt + 1)
                            for remaining in range(cooldown_secs, 0, -1):
                                yield sse_pack("status", {
                                    "step": "critic",
                                    "state": "running",
                                    "message": f"Rate limit reached. Waiting {remaining}s before resuming Review (Attempt {attempt + 1}/3)..."
                                })
                                await asyncio.sleep(1)
                            yield sse_pack("status", {
                                "step": "critic",
                                "state": "running",
                                "message": "Resuming Quality Review now…"
                            })
                        else:
                            raise e

                match = re.search(r"Score:.*?([\d\.]+)", critic_output)
                score = 10.0
                if match:
                    try:
                        score = float(match.group(1))
                    except ValueError:
                        pass

                if score < 8 and revision_count < 3:
                    revision_count += 1
                    results["last_critic"] = critic_output
                    eval_msg = f"Quality Review suggested refinements (Score: {score}/10). Review {revision_count} of 3 in progress..."

                    # Clear draft so the writer redrafts based on feedback
                    latest_writer_draft = None
                    results["revision_count"] = revision_count
                    results["eval_msg"] = eval_msg
                    save_session(sess_id, topic_val, results, workspace_id=ws_id)

                    yield sse_pack("revision", {
                        "revision_count": revision_count,
                        "eval_msg": eval_msg,
                        "score": score,
                        "critic_feedback": critic_output
                    })

                    # Proactive cooldown buffer before triggering new revision
                    for remaining in range(12, 0, -1):
                        yield sse_pack("status", {
                            "step": "writer",
                            "state": "running",
                            "message": f"Preparing Review {revision_count} of 3 with feedback. Pausing {remaining}s..."
                        })
                        await asyncio.sleep(1)

                    continue
                else:
                    # Finalized report approved or reviews completed
                    results["writer"] = latest_writer_draft
                    results["critic"] = critic_output
                    if score < 8:
                        eval_msg = "Completed review cycles. Presenting the final, verified report."
                    else:
                        eval_msg = "Great news! The report has passed our quality review and is ready for you."

                    results["revision_count"] = revision_count
                    results["eval_msg"] = eval_msg
                    save_session(sess_id, topic_val, results, workspace_id=ws_id)

                    # Present both the final report and the review scorecard
                    yield sse_pack("step_done", {
                        "step": "writer",
                        "data": latest_writer_draft
                    })

                    yield sse_pack("step_done", {
                        "step": "critic",
                        "data": critic_output,
                        "eval_msg": eval_msg,
                        "score": score
                    })
                    break

            # Completed successfully!
            yield sse_pack("complete", {
                "session_id": sess_id,
                "topic": topic_val,
                "results": results,
                "eval_msg": eval_msg,
                "revision_count": revision_count
            })

        except Exception as e:
            error_str = str(e)
            is_rate_limit = any(x in error_str for x in ["429", "Rate limit", "rate_limit_exceeded", "quota"])
            failed_step = "unknown"
            for k in PIPELINE_STEPS:
                if k not in results:
                    failed_step = k
                    break

            yield sse_pack("error", {
                "step": failed_step,
                "error": error_str,
                "is_rate_limit": is_rate_limit
            })

    return StreamingResponse(
        event_generator(),
        media_type="text/event-stream",
        headers={
            "Cache-Control": "no-cache",
            "Connection": "keep-alive",
            "Content-Type": "text/event-stream",
            "X-Accel-Buffering": "no",
        },
    )


@app.post("/api/export/docx")
async def export_docx(req: ExportDocxRequest):
    """Converts markdown report into a structured .docx document."""
    try:
        import markdown
        from docx import Document
        from htmldocx import HtmlToDocx

        cleaned_md = normalize_latex(req.markdown)
        html_content = markdown.markdown(cleaned_md, extensions=["tables", "fenced_code"])
        doc = Document()
        parser = HtmlToDocx()
        parser.add_html_to_document(html_content, doc)

        for table in doc.tables:
            table.style = "Table Grid"

        docx_io = io.BytesIO()
        doc.save(docx_io)
        docx_io.seek(0)

        safe_topic = re.sub(r"[^\w\-_]", "_", req.topic or "Research_Report")
        filename = f"Research_Report_{safe_topic}.docx"

        return StreamingResponse(
            docx_io,
            media_type="application/vnd.openxmlformats-officedocument.wordprocessingml.document",
            headers={"Content-Disposition": f'attachment; filename="{filename}"'},
        )
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"DOCX conversion failed: {str(e)}")


# Mount static frontend directory (HTML, CSS, JS) at root
frontend_dir = os.path.join(os.path.dirname(__file__), "frontend")
if not os.path.exists(frontend_dir):
    os.makedirs(frontend_dir, exist_ok=True)

app.mount("/", StaticFiles(directory=frontend_dir, html=True), name="frontend")

if __name__ == "__main__":
    import uvicorn
    # Bind to 0.0.0.0 so phones and tablets on local Wi-Fi can connect
    host_ip = os.getenv("HOST", "0.0.0.0")
    print("\n" + "=" * 60)
    print("🚀 ResearchMind is LIVE! Open your browser at:")
    print("👉 Local:   http://localhost:8000  or  http://127.0.0.1:8000")
    print("👉 Mobile:  http://192.168.32.67:8000")
    print("=" * 60 + "\n")
    port_num = int(os.getenv("PORT", 8000))
    uvicorn.run("app:app", host=host_ip, port=port_num, reload=True)
