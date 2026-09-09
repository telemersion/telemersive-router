#!/bin/bash
#
# Runs the switchboard's automated tests. They need nothing but python3 and the
# switchboard's own dependencies, and they bind UDP ports in the 31990 range on
# localhost. Pass a path to test a different checkout of the switchboard, which
# is useful for comparing behaviour before and after a change:
#
#   ./run-tests.sh                    # test the switchboard next to this script
#   ./run-tests.sh /tmp/old/switchboard
#
set -u

TESTS_DIR="$(cd "$(dirname "$0")" && pwd)"
SWITCHBOARD_DIR="${1:-$(dirname "$TESTS_DIR")}"

# forking a process that has already initialised the objc runtime is refused by
# default on macos; the deployment target (debian) is unaffected either way
if [ "$(uname)" = "Darwin" ]; then
    export OBJC_DISABLE_INITIALIZE_FORK_SAFETY=YES
fi

failed=0
for test in "$TESTS_DIR"/test_*.py; do
    echo "--- $(basename "$test") ---"
    if ! python3 "$test" "$SWITCHBOARD_DIR"; then
        failed=1
    fi
    echo ""
done

if [ "$failed" -eq 0 ]; then
    echo "All tests passed."
else
    echo "Some tests FAILED."
fi
exit "$failed"
