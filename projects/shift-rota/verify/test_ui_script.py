from playwright.sync_api import expect


def goto_script(page):
    page.goto("/script")


def test_c_3_1_script_happy_path_runs_and_logs_4(page):
    # Enter a 4-line script and run; expect idle, log-count 4, first row contains alert, last contains resolve
    goto_script(page)
    page.get_by_test_id("script-input").fill("alert\ntimeout\nack Beth\nresolve")
    page.get_by_test_id("btn-run-script").click()
    expect(page.get_by_test_id("mode")).to_have_text("idle")
    expect(page.get_by_test_id("log-count")).to_have_text("4")
    rows = page.locator('[data-testid^="log-row-"]')
    # Wait for 4 rows, then assert first and last contents
    expect(rows).to_have_count(4)
    expect(rows.nth(0)).to_contain_text("alert")
    expect(rows.nth(3)).to_contain_text("resolve")


def test_c_3_2_script_unknown_actor_errors(page):
    goto_script(page)
    page.get_by_test_id("script-input").fill("ack Dana")
    page.get_by_test_id("btn-run-script").click()
    expect(page.get_by_test_id("script-error")).to_contain_text("unknown actor Dana")


def test_c_3_3_script_illegal_transition_resolve_errors(page):
    goto_script(page)
    page.get_by_test_id("script-input").fill("resolve")
    page.get_by_test_id("btn-run-script").click()
    expect(page.get_by_test_id("script-error")).to_contain_text("illegal transition")


def test_c_3_4_script_wrong_actor_ack_errors(page):
    goto_script(page)
    page.get_by_test_id("script-input").fill("alert\nack Beth")
    page.get_by_test_id("btn-run-script").click()
    expect(page.get_by_test_id("script-error")).to_contain_text("only Alex can ack")


def test_c_3_5_script_stops_on_first_error_after_alert(page):
    goto_script(page)
    page.get_by_test_id("script-input").fill("alert\nack Dana\ntimeout")
    page.get_by_test_id("btn-run-script").click()
    expect(page.get_by_test_id("log-count")).to_have_text("1")
    expect(page.get_by_test_id("script-error")).to_contain_text("unknown actor Dana")
