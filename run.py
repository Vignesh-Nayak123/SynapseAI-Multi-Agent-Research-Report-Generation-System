from __future__ import annotations

import uvicorn


def main() -> None:
    """Entrypoint for launching the FastAPI server."""
    uvicorn.run("src.api:app", host="0.0.0.0", port=8000, reload=False)


if __name__ == "__main__":
    main()
