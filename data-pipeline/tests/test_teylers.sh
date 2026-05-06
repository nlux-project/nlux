#!/bin/bash
# Validates Teylers Museum records and source-level API entities.

set -euo pipefail

cd /Users/lux/data-pipeline

# ----------------------------------------
# Test: Rode paradijsvogel
# ----------------------------------------
# /Users/lux/data-pipeline/data/input/teylers/41634.json
# http://localhost:8088/view/object/f3b67ecf-52d7-4493-9576-ffc022e81d03
# http://localhost:8000/data/object/f3b67ecf-52d7-4493-9576-ffc022e81d03
/bin/bash /Users/jsoeterbroek/Development/nlux-project/nlux/data-pipeline/tests/test_teylers-record.sh 41634

# ----------------------------------------
# Test: Soldaat
# ----------------------------------------
# /Users/lux/data-pipeline/data/input/teylers/21916.json
# http://localhost:8088/view/object/00924cbb-d30b-4603-a300-8aebadbb27db
# http://localhost:8000/data/object/00924cbb-d30b-4603-a300-8aebadbb27db
/bin/bash /Users/jsoeterbroek/Development/nlux-project/nlux/data-pipeline/tests/test_teylers-record.sh 21916

# ----------------------------------------
# Test API search and resolvable references
# ----------------------------------------
TEST_PRIREF="41634" TEYLERS_REQUIRE_LIVE=1 \
    uv run python -m unittest "tests.test_teylers_pipeline.TeylersPipelineIntegrationTest.test_api_record_has_resolvable_collection_and_owner"

TEST_PRIREF="41634" TEYLERS_REQUIRE_LIVE=1 \
    uv run python -m unittest "tests.test_teylers_pipeline.TeylersPipelineIntegrationTest.test_api_search_finds_collection_and_owner"

# ----------------------------------------
# Test Set: Teylers Museum collection
# ----------------------------------------
# http://localhost:8088/view/set/d435a0f6-1837-5d39-a545-f9b994e8464c
# http://localhost:8000/data/set/d435a0f6-1837-5d39-a545-f9b994e8464c
# preferred name: Teylers Museum collection, type: named collection
TEYLERS_REQUIRE_LIVE=1 \
    uv run python -m unittest "tests.test_teylers_pipeline.TeylersPipelineIntegrationTest.test_api_teylers_collection_record"

# ----------------------------------------
# Test Person: Bailliu, Peeter-Frans
# ----------------------------------------
# http://localhost:8088/view/person/dea612fd-103f-539a-85a2-20a9eb44ad0d
# http://localhost:8000/data/person/dea612fd-103f-539a-85a2-20a9eb44ad0d
TEYLERS_REQUIRE_LIVE=1 \
    uv run python -m unittest "tests.test_teylers_pipeline.TeylersPipelineIntegrationTest.test_api_bailliu_person_record"
