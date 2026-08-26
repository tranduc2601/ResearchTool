"""CLI entrypoint for research-tool."""

import typer

app = typer.Typer(
    name="research-tool",
    help="Autonomous Visual Information Explorer CLI",
    add_completion=False,
)


@app.callback()
def main() -> None:
    """Autonomous Visual Information Explorer."""


if __name__ == "__main__":
    app()
