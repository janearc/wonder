import sys

from wonder_local.lib.modengine import ModularInferenceEngine


def main():
    if len(sys.argv) < 2:
        print("Usage: wonder <method> [args...]")
        sys.exit(1)

    engine = ModularInferenceEngine()
    method = sys.argv[1]
    args = sys.argv[2:]

    try:
        result = engine.invoke(method, *args)
        if result is not None:
            engine.logger.debug(result)
    except Exception:
        engine.logger.exception(f"\u2717 Error during '{method}'")


if __name__ == "__main__":
    main()
