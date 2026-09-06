from playwright.sync_api import expect


def test_c_1_2_sc_skus_list_renders_8_rows(base_url, page):
    page.goto("/")
    # Wait for rows to render, then assert exact count
    expect(page.locator('[data-testid="sku-row"]')).to_have_count(8)
