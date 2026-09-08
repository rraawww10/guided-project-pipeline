# Round 1

Gate 1: rejected
Note: Row order contradicts itself, and it is not owned by any downstream checker.

1. PICK ONE ROW ORDER AND MAKE ALL THREE AGREE.
   Three places describe the same guesses list on sc-board and they disagree:
   - cut-ui-render-rows (Session 2): "most-recent-first order"
   - cut-ui-replay-apply (Session 4): "the first step guesses ... in order of play"
   - c-4-3 (Session 4): "shows exactly K guess rows from the start of the game"
   A student follows the Session 2 hint, then contradicts it in Session 4.
   ambiguity.md assigns this to test-runner. That is wrong: test_c_4_3 asserts
   only the row count (rows == 2), and no test in the suite asserts order at
   all. Nothing downstream catches this, so it must be fixed here.

2. PIN THE PEG SELECTORS IN sc-board.
   test_ui_board.py asks for this directly: "Selectors for pegs are not pinned;
   this test assumes accessible labels 'black peg' and 'white peg'. If the UI
   uses a different hook, pin it in the spec." Add aria-label black peg and
   aria-label white peg to the sc-board elements.

3. PIN THE TURN CONTROL ELEMENT.
   c-4-3 says only "Turn control"; the test assumes input type=range. State
   which element it is in sc-board.

4. GIVE THE PREVIOUS GUESSES LIST A STABLE TEST HOOK.
   Four tests count rows by measuring the longest UL on the page. This board
   has 6 colours, so a peg picker rendered as a UL would be measured instead.
   Name a hook such as data-testid guess-rows on the previous guesses list.
