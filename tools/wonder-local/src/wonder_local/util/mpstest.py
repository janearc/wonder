def mpstest(self, *args):
    if not self:
        raise RuntimeError("mpstest needs to be called from modengine.py")

    """just assess whether mps is working"""
    import torch

    if torch.backends.mps.is_available():
        if torch.backends.mps.is_built():
            self.logger.info("✅ MPS is available and built into this PyTorch install.")
        else:
            self.logger.info("⚠️ MPS is available but not correctly built into PyTorch.")
    else:
        self.logger.info("❌ MPS is not available on this system.")
