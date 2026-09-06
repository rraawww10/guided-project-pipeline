"""Helpers for ui-test-01 (Envelope Budget Allocator).

The app is already running; its URL arrives in BASE_URL. Nothing here starts a
server, and waits are Playwright retrying waits, never sleeps.

Selectors:
- Use exact visible strings the spec pins: labels like "Paycheck", headings
  "Scenario A" / "Scenario B", summary labels like "Total allocated" and
  "Remainder", and envelope names from the tests (e.g. "Rent").
- The spec does not pin data-testids for the rules editor. To keep tests
  writable before code exists, the entry helpers below try a small, conventional
  set of labelled controls. If none is present they raise a clear assertion
  pointing at the expected affordance. This records the gap without inventing a
  styling selector.

Ambiguities chosen (see ambiguity.md):
- A1 priority: assume each rule has a numeric priority where higher numbers are
  higher priority; ties break by ascending rule id.
- A2 cap applies to the rule's own contribution, not the envelope total.
- W1 Remainder = paycheck − sum of all rule contributions after caps, rounded
  to 2 decimals.
- W2 Eligible for remainder = all envelopes present in the allocation when no
  caps are present; otherwise those below their caps.
- W3 Distribute remainder in ascending envelope.id order; ids we use are the
  envelope names lowercased with dashes.

Session 3 choices:
- A3: The share URL encodes BOTH Scenario A and Scenario B; opening it restores
  both columns.
- A4: Each column shows its own Undo and Redo buttons that affect only that
  column.
"""
from __future__ import annotations

import os
import re
from typing import Mapping, Optional

from playwright.sync_api import Locator, Page, expect

BASE_URL = os.environ["BASE_URL"].rstrip("/")
LOAD_TIMEOUT = 20_000


def base_url() -> str:
    return BASE_URL


def open_main(page: Page) -> None:
    page.goto(f"{BASE_URL}/", wait_until="domcontentloaded")


def open_compare(page: Page) -> None:
    page.goto(f"{BASE_URL}/compare", wait_until="domcontentloaded")


def normalize(text: Optional[str]) -> str:
    return " ".join((text or "").split())


# --------------------------
# Column scoping for /compare
# --------------------------

def column_scope(page: Page, heading: str) -> Locator:
    """Return a container Locator for the column headed by `heading`.

    We look for a heading with the given text and use its nearest section/div
    ancestor as the column container; if none, fall back to its parent node.
    """
    h = page.get_by_role("heading", name=heading, exact=True)
    expect(h).to_be_attached(timeout=LOAD_TIMEOUT)
    # Playwright Python supports XPath locators via the `locator` method
    container = h.locator("xpath=ancestor::*[self::section or self::div][1]")
    try:
        if container.first.is_visible(timeout=500):
            return container.first
    except Exception:
        pass
    return h.locator("xpath=..")


def share_url_input(page: Page) -> Locator:
    return page.get_by_label("Share URL", exact=True)


# --------------------------
# Editor interactions (best effort; fail loudly if absent)
# --------------------------

def _fill_labeled_input(scope: Page | Locator, label: str, value: str) -> None:
    ctrl = scope.get_by_label(label, exact=True)
    expect(ctrl).to_be_attached(timeout=LOAD_TIMEOUT)
    ctrl.fill("")
    ctrl.type(value)


def _click_named_button(scope: Page | Locator, name: str) -> None:
    btn = scope.get_by_role("button", name=name, exact=True)
    expect(btn).to_be_enabled(timeout=LOAD_TIMEOUT)
    btn.click()


def set_paycheck(scope: Page | Locator, value: float) -> None:
    _fill_labeled_input(scope, "Paycheck", f"{value}")


def _try_row_form(scope: Page | Locator, fields: Mapping[str, str]) -> bool:
    """Try to add/edit a rule via a conventional labeled row form.

    Expected controls (any subset used by the rule kind):
    - Button to add a rule: one of "Add rule", "Add fixed rule",
      "Add percent rule", "Add capped rule".
    - Labeled inputs: "Envelope", "Rule ID", "Kind", "Amount", "Percent",
      "Cap", "Priority".
    - For Kind, tests will prefer to click a specific add button so Kind may be
      implicit; if a "Kind" select exists we fill it.
    """
    # Try common add buttons
    added = False
    for name in ("Add rule", "Add fixed rule", "Add percent rule", "Add capped rule"):
        button = scope.get_by_role("button", name=name, exact=True)
        try:
            if button.is_enabled(timeout=500):
                button.click()
                added = True
                break
        except Exception:
            pass
    # Fill known labeled fields if present
    for label, value in fields.items():
        try:
            ctrl = scope.get_by_label(label, exact=True)
            if ctrl.is_visible(timeout=500):
                ctrl.fill("")
                ctrl.type(value)
        except Exception:
            # not fatal; the editor may not expose this field by label
            continue
    return added or bool(fields)


def _try_json_textarea(scope: Page | Locator, rule_obj: Mapping[str, object]) -> bool:
    """Try to paste JSON into a textarea labeled "Rules" or "Rules JSON".

    Appends the given rule to any existing JSON array, or writes a one-element
    array if empty.
    """
    for label in ("Rules", "Rules JSON"):
        try:
            area = scope.get_by_label(label, exact=True)
            if area.is_visible(timeout=500):
                current = normalize(area.input_value(timeout=500) or "")
                if current.strip().startswith("["):
                    # naive append before the closing bracket
                    before = current.rstrip().rstrip("]").rstrip()
                    json_text = (before + (", " if before.endswith("}") else "")
                                 + str(rule_obj).replace("'", '"') + "]")
                else:
                    json_text = "[" + str(rule_obj).replace("'", '"') + "]"
                area.fill(json_text)
                return True
        except Exception:
            continue
    return False


def add_fixed_rule(scope: Page | Locator, rule_id: str, envelope: str, amount: float, *, priority: Optional[int] = None) -> None:
    fields = {"Rule ID": rule_id, "Envelope": envelope, "Amount": f"{amount}"}
    if priority is not None:
        fields["Priority"] = str(priority)
    if _try_row_form(scope, fields):
        return
    ok = _try_json_textarea(scope, {"id": rule_id, "envelopeId": _env_id(envelope), "kind": "fixed", "amount": amount, **({"priority": priority} if priority is not None else {})})
    assert ok, (
        "Could not find a rules editor the spec pins. Expected either labelled "
        "fields (Envelope/Amount[/Priority]) after an 'Add rule' button, or a "
        "textarea labelled 'Rules'/'Rules JSON' accepting an array of rule objects."
    )


def add_percent_rule(scope: Page | Locator, rule_id: str, envelope: str, percent: float, *, priority: Optional[int] = None, cap: Optional[float] = None) -> None:
    fields = {"Rule ID": rule_id, "Envelope": envelope, "Percent": f"{percent}"}
    if cap is not None:
        fields["Cap"] = f"{cap}"
    if priority is not None:
        fields["Priority"] = str(priority)
    if _try_row_form(scope, fields):
        return
    kind = "percent-cap" if cap is not None else "percent"
    rule = {"id": rule_id, "envelopeId": _env_id(envelope), "kind": kind, "percent": percent}
    if cap is not None:
        rule["cap"] = cap
    if priority is not None:
        rule["priority"] = priority
    ok = _try_json_textarea(scope, rule)
    assert ok, (
        "Could not find a rules editor to enter a percent rule. Expected "
        "labelled fields (Envelope/Percent[/Cap][/Priority]) or a 'Rules' JSON textarea."
    )


def _env_id(name: str) -> str:
    return name.strip().lower().replace(" ", "-")


# --------------------------
# Results reading
# --------------------------

def find_result_row(scope: Page | Locator, envelope: str) -> Locator:
    """Best-effort locate a single rendered result row for an envelope.

    Without pinned testids, match any element likely to be a row (li/tr/div with
    role=row) whose text contains the envelope name and a money amount.
    """
    name = envelope
    amount_pat = r"-?\d+\.?\d{2}"
    # candidate containers in likely DOM order
    candidates = scope.locator("li, tr, [role=row], div").filter(has_text=re.compile(fr"{re.escape(name)}.*{amount_pat}|{amount_pat}.*{re.escape(name)}"))
    expect(candidates.first).to_be_attached(timeout=LOAD_TIMEOUT)
    return candidates.first


def read_amount_from_text(text: str) -> str:
    m = re.search(r"-?\d+\.\d{2}", normalize(text))
    assert m, f"no amount found in: {text!r}"
    return m.group(0)


def result_amount(scope: Page | Locator, envelope: str) -> str:
    row = find_result_row(scope, envelope)
    return read_amount_from_text(row.text_content(timeout=LOAD_TIMEOUT) or "")


def rationale_toggle(scope: Page | Locator) -> Locator:
    return scope.get_by_role("button", name=re.compile(r"^Rationale$|^Show rationale$|^Details$"))


def expand_envelope_details(scope: Page | Locator, envelope: str) -> Locator:
    row = find_result_row(scope, envelope)
    # click anywhere on the row, or a nested disclosure button if present
    try:
        row.click()
    except Exception:
        try:
            row.get_by_role("button").click()
        except Exception:
            pass
    return row


def rationale_lines_near(scope: Page | Locator, envelope: str) -> list[str]:
    row = expand_envelope_details(scope, envelope)
    # read nearby text blocks after expansion
    nearby = row.locator("..").locator("p, li, div")
    texts = [normalize(t) for t in nearby.all_text_contents()]
    return [t for t in texts if t]
