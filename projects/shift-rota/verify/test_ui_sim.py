from playwright.sync_api import expect


def goto_sim(page):
    page.goto("/")


def test_c_1_1_initial_idle_no_current(page):
    # sc-sim initial load shows mode "idle" and no current element
    goto_sim(page)
    mode = page.get_by_test_id("mode")
    expect(mode).to_have_text("idle")
    current = page.get_by_test_id("current")
    expect(current).to_have_count(0)


def test_c_1_2_alert_sets_current_and_mode(page):
    # After clicking Alert, current is Alex and mode is alerting
    goto_sim(page)
    page.get_by_test_id("btn-alert").click()
    current = page.get_by_test_id("current")
    expect(current).to_have_text("Alex")
    mode = page.get_by_test_id("mode")
    expect(mode).to_have_text("alerting")


def test_c_2_1_ack_by_alex_logs_and_keeps_current(page):
    # Alert -> select Alex -> Ack keeps current Alex, mode alerting, and logs ack by Alex
    goto_sim(page)
    page.get_by_test_id("btn-alert").click()
    actor = page.get_by_test_id("actor-select")
    actor.select_option(label="Alex")
    page.get_by_test_id("btn-ack").click()
    expect(page.get_by_test_id("mode")).to_have_text("alerting")
    expect(page.get_by_test_id("current")).to_have_text("Alex")
    # Do not depend on row count; assert presence of the expected log text
    expect(page.get_by_text("ack by Alex")).to_be_visible()


def test_c_2_2_timeout_escalates_to_beth(page):
    # Alert -> Timeout escalates current to Beth
    goto_sim(page)
    page.get_by_test_id("btn-alert").click()
    page.get_by_test_id("btn-timeout").click()
    expect(page.get_by_test_id("current")).to_have_text("Beth")


def test_c_2_3_wrong_actor_ack_shows_error_and_keeps_current(page):
    # Alert -> select Beth -> Ack shows error and current stays Alex
    goto_sim(page)
    page.get_by_test_id("btn-alert").click()
    page.get_by_test_id("actor-select").select_option(label="Beth")
    page.get_by_test_id("btn-ack").click()
    # Exact string is pinned by the spec text
    expect(page.get_by_text("only Alex can ack")).to_be_visible()
    expect(page.get_by_test_id("current")).to_have_text("Alex")


def test_c_2_4_resolve_returns_to_idle_no_current(page):
    """Alert -> Resolve returns to idle and removes the current element.

    The end state asserted here - idle, no current - is also the STARTING
    state, so asserting it alone passes on a skeleton where neither click does
    anything: the page simply never left idle. Pinning the alerting state in
    between is what makes the return to idle a transition rather than a
    coincidence.
    """
    goto_sim(page)
    page.get_by_test_id("btn-alert").click()
    # the alert must actually have taken effect, or "back to idle" proves nothing
    expect(page.get_by_test_id("mode")).to_have_text("alerting")
    expect(page.get_by_test_id("current")).to_have_text("Alex")
    page.get_by_test_id("btn-resolve").click()
    expect(page.get_by_test_id("mode")).to_have_text("idle")
    expect(page.get_by_test_id("current")).to_have_count(0)


def test_c_2_5_timeout_at_end_shows_error_and_keeps_chen(page):
    # Alert -> Timeout -> Timeout reaches Chen, next timeout errors and stays Chen
    goto_sim(page)
    page.get_by_test_id("btn-alert").click()
    page.get_by_test_id("btn-timeout").click()  # Alex -> Beth
    page.get_by_test_id("btn-timeout").click()  # Beth -> Chen
    page.get_by_test_id("btn-timeout").click()  # No further escalation
    expect(page.get_by_text("no further escalation")).to_be_visible()
    expect(page.get_by_test_id("current")).to_have_text("Chen")
