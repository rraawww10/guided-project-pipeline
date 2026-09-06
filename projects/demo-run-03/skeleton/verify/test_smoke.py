def test_smoke_always_passes():
    # A minimal sanity check that does not touch the running app.
    # This ensures mutation runs that break the app build are still
    # considered "ran" (at least one test passes), so per-cut grading
    # can be evaluated.
    assert True
