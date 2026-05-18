LUX_WORKDIR ?= /Users/lux/data-pipeline
CONFIG_CACHE_DIR ?= $(LUX_WORKDIR)/config/config_cache

SYNC_CONFIG_FILES := \
	docs/sample_config/nha-c359.json \

SYNC_FILES := \
	experiments/ai-enrichment/README.md \
	experiments/ai-enrichment/ai-enrichment.py \
	experiments/ai-enrichment/objects.example.txt \
	experiments/ai-enrichment/prompt.md \
	harvest-nha.py \
	harvest-nha.sh \
	manage-data.py \
	pipeline/process/ai_enrichment.py \
	pipeline/process/export_splitting.py \
	pipeline/sources/museums/nha/mapper.py \
	pipeline/sources/museums/nha/c359/__init__.py \
	pipeline/sources/museums/nha/c359/fetcher.py \
	pipeline/sources/museums/nha/c359/loader.py \
	pipeline/sources/museums/nha/c359/mapper.py \
	pipeline/sources/museums/nha/c1477/mapper.py \
	pipeline/sources/museums/nha/c480/mapper.py \
	pipeline/sources/museums/nha/c587/mapper.py \
	tests/test_ai_enrichment_cli.py \
	tests/test_nha_pipeline.py

SYNC_DIRS :=

.PHONY: help dry-run sync sync-config sync-files sync-dirs

help:
	@echo "Usage:"
	@echo "  make dry-run              Show files and dirs that would be copied"
	@echo "  make sync                 Copy listed files and dirs to $(LUX_WORKDIR)"
	@echo "  make sync LUX_WORKDIR=/path/to/workdir"

dry-run:
	@echo "Target: $(LUX_WORKDIR)"
	@echo "Config cache: $(CONFIG_CACHE_DIR)"
	@for path in $(SYNC_CONFIG_FILES); do \
		echo "config $$path -> $(CONFIG_CACHE_DIR)/$$(basename "$$path")"; \
	done
	@for path in $(SYNC_FILES); do \
		echo "file $$path -> $(LUX_WORKDIR)/$$path"; \
	done
	@for path in $(SYNC_DIRS); do \
		echo "dir  $$path -> $(LUX_WORKDIR)/$$path"; \
	done

sync: sync-config sync-files sync-dirs

sync-config:
	@mkdir -p "$(CONFIG_CACHE_DIR)"
	@for path in $(SYNC_CONFIG_FILES); do \
		cp "$$path" "$(CONFIG_CACHE_DIR)/$$(basename "$$path")"; \
		echo "copied $$path -> $(CONFIG_CACHE_DIR)/$$(basename "$$path")"; \
	done

sync-files:
	@for path in $(SYNC_FILES); do \
		mkdir -p "$(LUX_WORKDIR)/$$(dirname "$$path")"; \
		cp "$$path" "$(LUX_WORKDIR)/$$path"; \
		echo "copied $$path"; \
	done

sync-dirs:
	@for path in $(SYNC_DIRS); do \
		mkdir -p "$(LUX_WORKDIR)/$$(dirname "$$path")"; \
		cp -R "$$path" "$(LUX_WORKDIR)/$$(dirname "$$path")/"; \
		echo "copied $$path"; \
	done
