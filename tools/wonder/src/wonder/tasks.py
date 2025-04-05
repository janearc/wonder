from invoke import task, Program
from pathlib import Path
import shutil
import subprocess
from typing import Optional
import yaml
from rich.console import Console
from rich.table import Table

WONDER_ROOT = Path(__file__).parent.parent.parent.parent.parent
GIZZARD_OUTPUT = WONDER_ROOT / "gizzard-output"
DOCS_DIR = WONDER_ROOT / "docs"
PICOKERNEL_DIR = WONDER_ROOT / "kernels" / "pico"

console = Console()

# Create program instance for CLI
program = Program(
    namespace=None,
    version='0.1.0',
    name='wonder'
)

@task
def list_picokernels(ctx):
    """List all available picokernel applications and their descriptions."""
    if not PICOKERNEL_DIR.exists():
        print("❌ No picokernels directory found")
        return
    
    kernels = list(PICOKERNEL_DIR.glob("*.yaml"))
    if not kernels:
        print("No picokernel applications found in kernels/pico")
        return
    
    table = Table(title="Available Picokernel Applications")
    table.add_column("Name", style="cyan")
    table.add_column("Description", style="green")
    
    for kernel_path in sorted(kernels):
        try:
            with open(kernel_path) as f:
                kernel_data = yaml.safe_load(f)
                name = kernel_path.stem
                # Get the first key in the YAML as the picokernel key
                picokernel_key = next(iter(kernel_data.keys()))
                description = kernel_data[picokernel_key].get('description', 'No description available')
                table.add_row(name, description)
        except Exception as e:
            table.add_row(kernel_path.stem, f"[red]Error reading kernel: {e}[/red]")
    
    console.print(table)

@task
def refine(ctx, kernel_name: str, output_path: Optional[str] = None):
    """Generate a refined-kernel from a picokernel application.
    
    Args:
        kernel_name: Name of the picokernel application (without .yaml extension)
        output_path: Optional output path for the refined-kernel
    """
    kernel_path = PICOKERNEL_DIR / f"{kernel_name}.yaml"
    if not kernel_path.exists():
        print(f"❌ Picokernel '{kernel_name}' not found in {PICOKERNEL_DIR}")
        print("\nAvailable picokernels:")
        list_picokernels(ctx)
        return
    
    if not output_path:
        output_path = GIZZARD_OUTPUT / f"{kernel_name}.refined-kernel.yaml"
    
    GIZZARD_OUTPUT.mkdir(exist_ok=True)
    print(f"🔄 Refining {kernel_name} picokernel...")
    ctx.run(f"WONDER_ROOT={WONDER_ROOT} gizzard process {kernel_path} {output_path}")

@task
def clean(ctx):
    """Clean build artifacts and temporary files."""
    patterns = [
        "**/__pycache__",
        "**/*.pyc",
        "**/*.pyo",
        "**/*.pyd",
        "**/.pytest_cache",
        "**/.coverage",
        "**/.mypy_cache",
        "**/build",
        "**/dist",
        "**/*.egg-info",
    ]
    for pattern in patterns:
        for path in WONDER_ROOT.glob(pattern):
            if path.is_file():
                path.unlink()
            elif path.is_dir():
                shutil.rmtree(path)
    print("✨ Cleaned build artifacts")

@task
def format(ctx):
    """Format code using black and isort."""
    print("🎨 Formatting code...")
    ctx.run("black .")
    ctx.run("isort .")

@task
def lint(ctx):
    """Run linting and type checking."""
    print("🔍 Running mypy...")
    ctx.run("mypy tools/gizzard/src")
    print("✅ Type checking passed")

@task
def test(ctx):
    """Run tests with pytest."""
    print("🧪 Running tests...")
    ctx.run("pytest tools/gizzard/tests -v")

@task
def docs(ctx):
    """Generate documentation using pdoc."""
    print("📚 Generating documentation...")
    docs_api = DOCS_DIR / "api"
    docs_api.mkdir(parents=True, exist_ok=True)
    
    # Generate API documentation
    ctx.run(f"pdoc --html --output-dir {docs_api} tools/gizzard/src/gizzard")
    
    # Update README with CLI help
    readme = WONDER_ROOT / "README.md"
    cli_help = subprocess.check_output(["gizzard", "--help"]).decode()
    
    with open(readme, "r") as f:
        content = f.read()
        
    # Update or add CLI section
    cli_section = "## Command Line Interface\n\n```\n" + cli_help + "\n```"
    if "## Command Line Interface" in content:
        content = content.split("## Command Line Interface")[0] + cli_section
    else:
        content += "\n\n" + cli_section
        
    with open(readme, "w") as f:
        f.write(content)
    
    print("✅ Documentation generated")

@task(pre=[clean, format, lint, test])
def build(ctx):
    """Build the project (runs clean, format, lint, and test)."""
    print("🏗️  Building project...")
    ctx.run("poetry build")

@task
def install(ctx):
    """Install the project in development mode."""
    print("📦 Installing dependencies...")
    ctx.run("poetry install")
    
    # Move gizzard script to new location
    old_gizzard = WONDER_ROOT / "sigil/core/system/bin/gizzard"
    new_gizzard = WONDER_ROOT / "tools/gizzard/src/gizzard"
    new_gizzard.mkdir(parents=True, exist_ok=True)
    
    if old_gizzard.exists():
        print("🚚 Moving gizzard script to new location...")
        shutil.move(old_gizzard, new_gizzard / "processor.py")
        # Create __init__.py
        (new_gizzard / "__init__.py").touch()
        
        # Remove old directory if empty
        try:
            old_gizzard.parent.rmdir()
            old_gizzard.parent.parent.rmdir()
            old_gizzard.parent.parent.parent.rmdir()
        except OSError:
            pass  # Directory not empty
    
    print("✅ Installation complete")

@task
def example(ctx):
    """Example: Refine the Cinder application's kernel."""
    refine(ctx, "cinder")

@task
def clean_venv(ctx):
    """Clean virtual environment and reinstall dependencies"""
    print("🧹 Cleaning virtual environment...")
    ctx.run("rm -rf .venv")
    ctx.run("./scripts/setup-venv.sh")
    print("✨ Virtual environment cleaned and reinstalled!") 