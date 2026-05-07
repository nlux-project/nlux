#!/bin/bash
# Validates NHA C587 records after each step -- exits on first failure.

set -euo pipefail

cd /Users/lux/data-pipeline

TEST_NHA_C587_ID1="${1:-F7DDF7EEFB8E11DF9E4D523BC2E286E2}"
TEST_NHA_C587_ID2="${1:-F7A6959CFB8E11DF9E4D523BC2E286E2}"

echo "==> Testing NHA C587 ..."
echo "==> Testing mapper and fetcher configuration ..."
TEST_NHA_C587_ID="$TEST_NHA_C587_ID1" NHA_C587_REQUIRE_LIVE=1 \
    uv run python -m unittest "tests.test_nha_pipeline.NhaC587PipelineIntegrationTest.test_fetcher_builds_filtered_memorix_requests"
TEST_NHA_C587_ID="$TEST_NHA_C587_ID1" NHA_C587_REQUIRE_LIVE=1 \
    uv run python -m unittest "tests.test_nha_pipeline.NhaC587PipelineIntegrationTest.test_mapper_transforms_record"

/bin/bash /Users/jsoeterbroek/Development/nlux-project/nlux/data-pipeline/tests/test_nha-pipeline.sh "$TEST_NHA_C587_ID1"
/bin/bash /Users/jsoeterbroek/Development/nlux-project/nlux/data-pipeline/tests/test_nha-pipeline.sh "$TEST_NHA_C587_ID2"

# ----------------------------------------
# Test Person: Maarten van Heemskerk
# ----------------------------------------
# The C587 portrait object should also produce a searchable Person result.
NHA_C587_REQUIRE_LIVE=1 \
    uv run python -m unittest "tests.test_nha_pipeline.NhaC587PipelineIntegrationTest.test_api_mvanheemskerk_person_record"
