from pathlib import Path
from wonder_local.lib.profiling import profile_sigil, SigilProfile

def profile(self, file_path: str) -> SigilProfile:
    try:
        with open(file_path, "r", encoding="utf-8") as f:
            md = f.read()
    except Exception as e:
        self.logger.error(f"❌ Failed to read file '{file_path}': {e}")
        return

    sigil_stem = Path(file_path).stem
    
    profiled = profile_sigil(self, md, sigil_stem)

    self.logger.info(f"📊 Profile ({sigil_stem}): token_count: {profiled.token_count}")
    self.logger.info(f"📊 Profile ({sigil_stem}): zipf_avg: {profiled.zipf_avg}")
    self.logger.info(f"📊 Profile ({sigil_stem}): rarity_pos: {profiled.rarity_pos}")
    self.logger.info(f"📊 Profile ({sigil_stem}): rare_terms: {profiled.rare_terms}")

    return profiled
