import typer
from pathlib import Path
from rich import print
from rich.console import Console
from rich.table import Table
from typing import Optional
from .processor import GizzardProcessor

app = typer.Typer(
    name="gizzard",
    help="Wonder Framework processor for generating refined-kernels from sigil content.",
    add_completion=False,
)

console = Console()

# Get the package directory
PACKAGE_DIR = Path(__file__).parent.parent.parent.parent
CONFIG_DIR = PACKAGE_DIR / "config"

def version_callback(value: bool):
    """Print version information."""
    if value:
        from importlib.metadata import version
        try:
            v = version("wonder")
            print(f"[bold]Gizzard[/bold] version: {v}")
        except:
            print("[bold]Gizzard[/bold] version: development")
        raise typer.Exit()

@app.callback()
def main(
    version: bool = typer.Option(
        None,
        "--version",
        "-V",
        help="Show version information.",
        callback=version_callback,
        is_eager=True,
    )
):
    """Wonder Framework processor for generating refined-kernels from sigil content."""
    pass

@app.command()
def process(
    kernel_path: Path = typer.Argument(
        ...,
        help="Path to the source kernel configuration file",
        exists=True,
        file_okay=True,
        dir_okay=False,
        resolve_path=True,
    ),
    output_path: Optional[Path] = typer.Option(
        None,
        "--output",
        "-o",
        help="Output path for refined-kernel (default: gizzard-output/<kernel_name>.refined-kernel.yaml)",
    ),
    config_path: Path = typer.Option(
        CONFIG_DIR / "gizzard.yaml",
        "--config",
        "-c",
        help="Path to gizzard configuration file",
        exists=True,
    ),
    schema_path: Path = typer.Option(
        CONFIG_DIR / "schema.yaml",
        "--schema",
        "-s",
        help="Path to JSON schema file",
        exists=True,
    ),
    verbose: bool = typer.Option(
        False,
        "--verbose",
        "-v",
        help="Enable verbose output",
    ),
):
    """Process a kernel configuration file into a refined-kernel, optimizing content and extracting relationships."""
    try:
        if not output_path:
            output_path = Path("gizzard-output") / f"{kernel_path.stem}.refined-kernel.yaml"
        
        output_path.parent.mkdir(parents=True, exist_ok=True)
        
        processor = GizzardProcessor(str(config_path), str(schema_path))
        
        with console.status("[bold green]Generating refined-kernel..."):
            processor.process_kernel(kernel_path, output_path)
        
        # Show statistics
        stats = processor.get_statistics()
        
        table = Table(title="Refinement Statistics")
        table.add_column("Metric", style="cyan")
        table.add_column("Value", justify="right", style="green")
        
        table.add_row("Files Processed", str(stats["files_processed"]))
        table.add_row("Total Original Tokens", str(stats["total_original_tokens"]))
        table.add_row("Total Refined Tokens", str(stats["total_processed_tokens"]))
        table.add_row(
            "Refinement Ratio",
            f"{stats['average_reduction_percentage']:.2f}%"
        )
        table.add_row("Relationships Extracted", str(stats["relationships_extracted"]))
        
        console.print(table)
        
        print(f"\n✨ [bold green]Success![/bold green] Refined-kernel written to: {output_path}")
        
    except Exception as e:
        print(f"[bold red]Error:[/bold red] {str(e)}")
        raise typer.Exit(1)

@app.command()
def validate(
    kernel_path: Path = typer.Argument(
        ...,
        help="Path to the kernel configuration file to validate",
        exists=True,
        file_okay=True,
        dir_okay=False,
        resolve_path=True,
    ),
    schema_path: Path = typer.Option(
        CONFIG_DIR / "schema.yaml",
        "--schema",
        "-s",
        help="Path to JSON schema file",
    ),
):
    """Validate a kernel or refined-kernel configuration file against the schema."""
    try:
        processor = GizzardProcessor(None, schema_path)
        processor.validate_kernel(kernel_path)
        print(f"[bold green]✓[/bold green] Configuration is valid: {kernel_path}")
    except Exception as e:
        print(f"[bold red]✗[/bold red] Validation failed: {str(e)}")
        raise typer.Exit(1)

if __name__ == "__main__":
    app() 