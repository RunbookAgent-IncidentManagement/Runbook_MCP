#!/usr/bin/env python3
"""
Kubernetes MCP Server — FastMCP stdio protocol implementation.
Exposes Kubernetes operations as MCP tools over stdio transport.
Supports K8S_DRY_RUN=true for testing without an active cluster.
"""
import os
import json
import subprocess
import sys

try:
    from fastmcp import FastMCP
except ImportError:
    try:
        from mcp.server.fastmcp import FastMCP
    except ImportError:
        try:
            from mcp.server import FastMCP
        except ImportError as err:
            print(f"[WARN] Real FastMCP package not loaded ({err}). Using fallback shim.", file=sys.stderr)
            class FastMCP:
                def __init__(self, name):
                    self.name = name
                    self.tools = {}

                def tool(self, func=None):
                    def decorator(f):
                        self.tools[f.__name__] = f
                        return f
                    return decorator(func) if func else decorator

                def run(self, transport="stdio"):
                    print(f"[{self.name}] Running over {transport} (shim)", file=sys.stderr)

mcp = FastMCP("kubernetes-mcp-server")

DEFAULT_NAMESPACE = os.getenv("K8S_NAMESPACE", "ecommerce")


def _is_dry_run() -> bool:
    """Read DRY_RUN at call time so env changes are reflected immediately."""
    return os.getenv("K8S_DRY_RUN", "false").lower() in ("true", "1", "yes")


def _is_force_unhealthy() -> bool:
    """Check if FORCE_UNHEALTHY simulation flag is active."""
    return os.getenv("FORCE_UNHEALTHY", "false").lower() in ("true", "1", "yes")


@mcp.tool()
def get_pod_logs(pod_name: str, namespace: str = DEFAULT_NAMESPACE, previous: bool = False) -> str:
    """Retrieve stdout/stderr logs from pods matching a deployment name. Set previous=True for crashed container logs."""
    if _is_dry_run():
        return f"[DRY_RUN] Logs for pod {pod_name} in namespace {namespace}:\njava.lang.OutOfMemoryError: Metaspace\nConnection refused to database: postgres:5432"

    # Find actual pod name via label selector (pod names have hash suffixes)
    find_cmd = ["kubectl", "get", "pods", "-n", namespace, "-l", f"app={pod_name}",
                "-o", "jsonpath={.items[0].metadata.name}"]
    try:
        find_res = subprocess.run(find_cmd, capture_output=True, text=True, timeout=10)
        actual_pod = find_res.stdout.strip()
        if not actual_pod:
            return json.dumps({"status": "error", "message": f"No pods found matching label app={pod_name}"})

        log_cmd = ["kubectl", "logs", actual_pod, "-n", namespace, "--tail=100"]
        if previous:
            log_cmd.append("--previous")

        res = subprocess.run(log_cmd, capture_output=True, text=True, timeout=15)
        return res.stdout or res.stderr or "No log output available."
    except Exception as exc:
        return f"Error executing kubectl logs: {exc}"


@mcp.tool()
def rollout_restart(deployment: str, namespace: str = DEFAULT_NAMESPACE) -> str:
    """Trigger a rolling restart of a Kubernetes deployment."""
    if _is_dry_run():
        return json.dumps({
            "status": "success",
            "action": "rollout_restart",
            "deployment": deployment,
            "namespace": namespace,
            "dry_run": True,
            "message": f"Deployment {deployment} restart initiated in dry-run mode."
        })

    cmd = ["kubectl", "rollout", "restart", f"deployment/{deployment}", "-n", namespace]
    try:
        res = subprocess.run(cmd, capture_output=True, text=True, timeout=30)
        return json.dumps({
            "status": "success" if res.returncode == 0 else "error",
            "action": "rollout_restart",
            "deployment": deployment,
            "namespace": namespace,
            "stdout": res.stdout.strip(),
            "stderr": res.stderr.strip()
        })
    except Exception as exc:
        return json.dumps({"status": "error", "message": str(exc)})


@mcp.tool()
def rollout_undo(deployment: str, namespace: str = DEFAULT_NAMESPACE) -> str:
    """Roll back a Kubernetes deployment to its previous stable revision."""
    if _is_dry_run():
        return json.dumps({
            "status": "success",
            "action": "rollout_undo",
            "deployment": deployment,
            "namespace": namespace,
            "dry_run": True,
            "message": f"Deployment {deployment} rolled back to previous revision in dry-run mode."
        })

    cmd = ["kubectl", "rollout", "undo", f"deployment/{deployment}", "-n", namespace]
    try:
        res = subprocess.run(cmd, capture_output=True, text=True, timeout=30)
        return json.dumps({
            "status": "success" if res.returncode == 0 else "error",
            "action": "rollout_undo",
            "deployment": deployment,
            "namespace": namespace,
            "stdout": res.stdout.strip(),
            "stderr": res.stderr.strip()
        })
    except Exception as exc:
        return json.dumps({"status": "error", "message": str(exc)})


@mcp.tool()
def scale_deployment(deployment: str, replicas: int = 4, namespace: str = DEFAULT_NAMESPACE) -> str:
    """Scale a Kubernetes deployment to the specified number of replicas."""
    if _is_dry_run():
        return json.dumps({
            "status": "success",
            "action": "scale_deployment",
            "deployment": deployment,
            "replicas": replicas,
            "namespace": namespace,
            "dry_run": True,
            "message": f"Deployment {deployment} scaled to {replicas} replicas in dry-run mode."
        })

    cmd = ["kubectl", "scale", f"deployment/{deployment}", f"--replicas={replicas}", "-n", namespace]
    try:
        res = subprocess.run(cmd, capture_output=True, text=True, timeout=30)
        return json.dumps({
            "status": "success" if res.returncode == 0 else "error",
            "action": "scale_deployment",
            "deployment": deployment,
            "replicas": replicas,
            "stdout": res.stdout.strip(),
            "stderr": res.stderr.strip()
        })
    except Exception as exc:
        return json.dumps({"status": "error", "message": str(exc)})


@mcp.tool()
def get_pod_status(pod_name: str, namespace: str = DEFAULT_NAMESPACE) -> str:
    """Check the health status and readiness probes of all pods matching a deployment/pod name."""
    force_fail = _is_force_unhealthy() or any(k in pod_name.lower() for k in ["broken", "unhealthy", "fail"])
    if _is_dry_run():
        return json.dumps({
            "status": "CrashLoopBackOff" if force_fail else "Running",
            "healthy": not force_fail,
            "pod": pod_name,
            "namespace": namespace,
            "ready_containers": "0/1" if force_fail else "1/1",
            "restarts": 5 if force_fail else 0,
            "dry_run": True
        })

    cmd = ["kubectl", "get", "pods", "-n", namespace, "-l", f"app={pod_name}", "-o", "json"]
    try:
        res = subprocess.run(cmd, capture_output=True, text=True, timeout=15)
        if res.returncode == 0 and res.stdout.strip():
            data = json.loads(res.stdout)
            items = data.get("items", [])

            # Filter out terminating pods
            active_pods = [p for p in items if p.get("metadata", {}).get("deletionTimestamp") is None]
            if not active_pods:
                return json.dumps({"status": "NotFound", "healthy": False, "pod": pod_name})

            # Aggregate health across all active pods
            all_healthy = True
            total_restarts = 0
            pod_summaries = []

            for pod in active_pods:
                phase = pod.get("status", {}).get("phase", "Unknown")
                container_statuses = pod.get("status", {}).get("containerStatuses", [])
                ready = all(cs.get("ready", False) for cs in container_statuses) if container_statuses else False
                restarts = sum(cs.get("restartCount", 0) for cs in container_statuses) if container_statuses else 0
                total_restarts += restarts

                pod_healthy = phase == "Running" and ready
                if not pod_healthy:
                    all_healthy = False

                pod_summaries.append({
                    "name": pod.get("metadata", {}).get("name"),
                    "phase": phase,
                    "ready": ready,
                    "restarts": restarts,
                    "healthy": pod_healthy
                })

            return json.dumps({
                "status": active_pods[0].get("status", {}).get("phase", "Unknown"),
                "healthy": all_healthy,
                "pod": pod_name,
                "namespace": namespace,
                "total_pods": len(active_pods),
                "total_restarts": total_restarts,
                "pods": pod_summaries
            })
        return json.dumps({"status": "NotFound", "healthy": False, "pod": pod_name})
    except Exception as exc:
        return json.dumps({"status": "Error", "healthy": False, "message": str(exc)})


if __name__ == "__main__":
    if "--sse" in sys.argv or os.getenv("MCP_TRANSPORT") == "sse":
        port = int(os.getenv("PORT", 8001))
        os.environ["FASTMCP_HOST"] = "0.0.0.0"
        os.environ["FASTMCP_PORT"] = str(port)
        print(f"🚀 Starting FastMCP Kubernetes Web/SSE Server on http://0.0.0.0:{port}")
        try:
            mcp.settings.host = "0.0.0.0"
            mcp.settings.port = port
        except Exception:
            pass
        mcp.run(transport="sse")
    else:
        mcp.run(transport="stdio")
