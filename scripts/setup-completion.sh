#!/bin/zsh

# Create zsh completion directory if it doesn't exist
ZSH_COMPLETION_DIR="${ZDOTDIR:-$HOME}/.zsh/completion"
mkdir -p "$ZSH_COMPLETION_DIR"

# Copy completion script
cp "$(dirname $0)/completion/_wonder" "$ZSH_COMPLETION_DIR/_wonder"

# Add completion directory to fpath if not already there
FPATH_LINE="fpath=($ZSH_COMPLETION_DIR \$fpath)"
ZSHRC="${ZDOTDIR:-$HOME}/.zshrc"

if ! grep -q "$FPATH_LINE" "$ZSHRC"; then
    echo "\n# Wonder completion" >> "$ZSHRC"
    echo "$FPATH_LINE" >> "$ZSHRC"
    echo "autoload -Uz compinit && compinit" >> "$ZSHRC"
fi

echo "✨ Zsh completion for wonder installed!"
echo "Please restart your shell or run:"
echo "  source ~/.zshrc" 