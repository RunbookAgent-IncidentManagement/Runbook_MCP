#!/usr/bin/env python3
"""
Local Kubernetes MCP Server (Free Mode)
Runs as a background sub-process managed by the LangGraph Python script.
Reads local ~/.kube/config and executes kubectl against the K3s cluster.
"""
import os
import json
import subprocess
import sys

CONFIG_PATH = os.path.expanduser("~/.kube/config")


def get_pod_logs(pod_name: str, namespace: str = "default") -> str:
    result = subprocess.run(
        ["kubectl", "logs", pod_name, "-n", namespace],
        capture_output=True,
        text=True,
    )
    return result.stdout or result.stderr


def rollout_restart(deployment: str, namespace: str = "default") -> dict:
    result = subprocess.run(
        ["kubectl", "rollout", "restart", f"deployment/{deployment}", "-n", namespace],
        capture_output=True,
        text=True,
    )
    return {"action": "rollout_restart", "deployment": deployment, "stdout": result.stdout, "stderr": result.stderr}


def rollout_undo(deployment: str, namespace: str = "default") -> dict:
    result = subprocess.run(
        ["kubectl", "rollout", "undo", f"deployment/{deployment}", "-n", namespace],
        capture_output=True,
        text=True,
    )
    return {"action": "rollout_undo", "deployment": deployment, "stdout": result.stdout, "stderr": result.stderr}


def scale_deployment(deployment: str, replicas: int = 6, namespace: str = "default") -> dict:
    result = subprocess.run(
        ["kubectl", "scale", f"deployment/{deployment}", f"--replicas={replicas}", "-n", namespace],
        capture_output=True,
        text=True,
    )
    return {"action": "scale", "deployment": deployment, "replicas": replicas, "stdout": result.stdout, "stderr": result.stderr}


def get_pod_status(pod_name: str, namespace: str = "default") -> dict:
    result = subprocess.run(
        ["kubectl", "get", "pod", pod_name, "-n", namespace, "-o", "json"],
        capture_output=True,
        text=True,
    )
    try:
        return {"status": json.loads(result.stdout), "pod": pod_name}
    except Exception:
        return {"status": "not_found", "pod": pod_name, "stderr": result.stderr}


if __name__ == "__main__":
    print("Kubernetes MCP Server (Free Mode) — Running locally with kubeconfig at:", CONFIG_PATH)
    # In the real architecture, this is launched as a background sub-process by langchain-mcp-adapters.
