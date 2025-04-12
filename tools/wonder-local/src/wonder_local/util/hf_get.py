import os

from huggingface_hub import snapshot_download


def hf_get(self, *args):

    if not args:
        self.logger.info(
            "[red]Please specify a model ID to download, e.g. meta-llama/Meta-Llama-3-8B-Instruct[/red]"
        )
        return

    model_id = args[0]
    cache_dir = os.path.expanduser("~/.cache/huggingface/hub")

    self.logger.info(f":inbox_tray: [cyan]Fetching model:[/cyan] {model_id}")

    try:
        path = snapshot_download(
            repo_id=model_id, cache_dir=cache_dir, resume_download=True
        )
        self.logger.info(f"[green]\u2713 Download complete:[/green] {path}")
    except Exception as e:
        self.logger.info(f"[red]\u2717 Failed to download:[/red] {e}")
