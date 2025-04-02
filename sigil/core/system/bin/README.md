# Gizzard Processor

Gizzard is a tool for processing and optimizing markdown files in the Wonder system. It reads files from specified sigil directories, processes their content, and outputs an optimized YAML file.

## Requirements

1. Python 3.x
2. Required packages (installed automatically by setup script):
   - pyyaml
   - jsonschema
3. Environment setup:
   ```bash
   # Set WONDER_ROOT to point to your wonder project root
   export WONDER_ROOT=/path/to/your/wonder/root
   ```

## Setup

1. First time setup:
   ```bash
   # Go to the bin directory
   cd sigil/core/system/bin
   
   # Run the setup script
   ./setup_gizzard.sh
   ```
   This will:
   - Create a Python virtual environment in the parent directory
   - Install required packages from requirements.txt
   - Make the gizzard script executable

2. Before using gizzard (each time):
   ```bash
   # Activate the virtual environment
   source ../venv/bin/activate
   
   # Make sure WONDER_ROOT is set
   echo $WONDER_ROOT
   ```

## Usage

Basic usage:
```bash
python3 gizzard <kernel_file> --output <output_file>
```

Example:
```bash
python3 gizzard ../../kernels/pico/cinder.yaml --output cinder_optimized.yaml
```

### What it does

1. Reads all markdown files from the sigil directories specified in the kernel file
2. Processes each file:
   - Extracts title and category
   - Processes content to reduce tokens
   - Handles relationships between concepts
3. Outputs a single YAML file containing:
   - Kernel metadata
   - Identity and actions
   - Processed content from all files
   - Relationships between concepts

### Output Format

The output YAML file will have this structure:
```yaml
kernel: <kernel_name>
metadata:
  repository: <repository_url>
  seed: <seed_file_path>
  identity: <identity_text>
  actions: <action_list>
content: |
  # Processed content from all files...
relationships:
  # List of relationships between concepts...
```

## Troubleshooting

If you get a "WONDER_ROOT not set" error:
1. Make sure you've set the WONDER_ROOT environment variable
2. Verify the path exists and is correct
3. The path should point to the root of your wonder project

If you get a "command not found" error:
1. Make sure you've activated the virtual environment
2. Make sure you're in the correct directory
3. Try running the setup script again

If you get import errors:
1. Make sure the virtual environment is activated
2. Try running `pip install -r requirements.txt` in the virtual environment

## Notes

- The virtual environment is in `sigil/core/system/venv/`
- You need to activate the virtual environment each time you open a new terminal
- The output file will be created in your current directory
- WONDER_ROOT must be set to the root directory of your wonder project 