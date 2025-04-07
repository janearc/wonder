# fine-tuned/

This directory holds the most recent fine-tuned weights for Wonder.

The model itself is **not tracked in git** due to size and sanctity.  
Artifacts include `.safetensors`, `.bin`, and other generated state.

This folder represents a **trained stance**, not just a file system path.

To regenerate or resume from here, use:

```bash
engine = LocalInferenceEngine(model_name="./fine-tuned")
engine.load_model()
```
