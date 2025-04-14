from wonder_local.config.modules import MODULE_CONFIG
from wonder_local.lib.modengine import ModularInferenceEngine

def run_tests(self):
    failures = []

    for name, config in MODULE_CONFIG.items():
        test_cases = config.get("tests")
        if not test_cases:
            continue

        for idx, case in enumerate(test_cases):
            test_args = case.get("input")
            expected = case.get("expected")

            # Normalize to a list of args if needed
            args = test_args if isinstance(test_args, list) else [test_args]

            self.logger.info(f"📝 Running test {idx+1} for: {name} with args: {args}")
            try:
                result = self.invoke(name, *args)

                if expected is not None:
                    # Loose match
                    assert expected in str(result), f"Expected '{expected}' in result, got: '{result}'"
                self.logger.info(f"✅ {name} test {idx+1} passed")
            except AssertionError as ae:
                self.logger.error(f"❌ {name} test {idx+1} failed assertion: {ae}")
                failures.append((name, idx + 1))
            except Exception as e:
                self.logger.error(f"❌ {name} test {idx+1} raised an error: {e}")
                failures.append((name, idx + 1))

    if failures:
        self.logger.warning("❗ Some tests failed:")
        for name, idx in failures:
            self.logger.warning(f"  - {name} test {idx}")
    else:
        self.logger.info("🎉 All module tests passed!")
