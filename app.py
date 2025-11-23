from __future__ import annotations

import os

import gradio as gr

from mcp_server.server import create_gradio_blocks

# Expose a demo/app object for Hugging Face Spaces auto-discovery
demo: gr.Blocks = create_gradio_blocks()
app: gr.Blocks = demo

if __name__ == "__main__":
    # Respect common env vars used by Spaces/containers
    host = os.getenv("GRADIO_SERVER_NAME") or os.getenv("HOST") or "0.0.0.0"
    port_str = os.getenv("GRADIO_SERVER_PORT") or os.getenv("PORT") or "7860"
    try:
        port = int(port_str)
    except Exception:
        port = 7860
    demo.launch(server_name=host, server_port=port, mcp_server=True)