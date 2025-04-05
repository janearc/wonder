# Gizzard

Wonder Framework processor for generating refined-kernels from sigil content.

## Overview

Gizzard is a specialized processor that:
- Processes picokernel configurations
- Extracts and optimizes relationships from sigil content
- Generates refined-kernels for the Wonder framework

## Installation

```bash
cd tools/gizzard
pip install -e .
```

## Usage

Gizzard can be used directly or through the Wonder CLI:

```bash
# Direct usage
gizzard process path/to/kernel.yaml

# Via Wonder CLI
wonder refine kernel-name
```

## Configuration

Gizzard uses two main configuration files:
- `config/gizzard.yaml` - Processing configuration
- `config/schema.yaml` - Schema validation

## Commands

- `gizzard process KERNEL_PATH` - Process a kernel into a refined-kernel
- `gizzard validate KERNEL_PATH` - Validate a kernel configuration 