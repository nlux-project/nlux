#!/bin/bash
# Validates Huis van Hilde records and source-level API entities.

set -euo pipefail

cd /Users/lux/data-pipeline

# ----------------------------------------
# Test: Roodbakkend geglazuurd:vuurtest/komfoor
# ----------------------------------------
# /Users/lux/data-pipeline/data/input/hvh/4564-09.json
# http://localhost:8088/view/object/c809d719-9b22-4bdc-a656-f0a51eafbc83
# http://localhost:8000/data/object/c809d719-9b22-4bdc-a656-f0a51eafbc83
/bin/bash /Users/jsoeterbroek/Development/nlux-project/nlux/data-pipeline/tests/test_hvh-record.sh 4564-09

# ----------------------------------------
# Test: Pseudo-muntfibula/bracteatenfibula
# ----------------------------------------
# /Users/lux/data-pipeline/data/input/hvh/5061-06.json
/bin/bash /Users/jsoeterbroek/Development/nlux-project/nlux/data-pipeline/tests/test_hvh-record.sh 5061-06

# ----------------------------------------
# Test API search and resolvable references
# ----------------------------------------
TEST_PRIREF="4564-09" HVH_REQUIRE_LIVE=1 \
    uv run python -m unittest "tests.test_hvh_pipeline.HvhPipelineIntegrationTest.test_api_record_has_resolvable_collection_and_owner"

TEST_PRIREF="4564-09" HVH_REQUIRE_LIVE=1 \
    uv run python -m unittest "tests.test_hvh_pipeline.HvhPipelineIntegrationTest.test_api_search_finds_collection_and_owner"

# ----------------------------------------
# Test Set: Huis van Hilde
# ----------------------------------------
# http://localhost:8088/view/set/5938ba10-2285-5b40-b5c4-ab17473021c3
# http://localhost:8000/data/set/5938ba10-2285-5b40-b5c4-ab17473021c3
# preferred name: Huis van Hilde, type: named collection
HVH_REQUIRE_LIVE=1 \
    uv run python -m unittest "tests.test_hvh_pipeline.HvhPipelineIntegrationTest.test_api_hvh_collection_record"

# ----------------------------------------
# Test Group: Provinciaal Depot voor Archeologie Noord-Holland
# ----------------------------------------
# HVH currently has Group/organization references, but no Person references.
# http://localhost:8000/data/group/e31c637a-00b2-541d-94f3-1730925ae40a
HVH_REQUIRE_LIVE=1 \
    uv run python -m unittest "tests.test_hvh_pipeline.HvhPipelineIntegrationTest.test_api_hvh_owner_group_record"
