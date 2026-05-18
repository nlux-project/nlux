LUX_WORKDIR ?= /Users/lux/data-pipeline

SYNC_FILES := \
	docs/sample_config/nha-c359.json \
	harvest-nha.py \
	harvest-nha.sh \
	pipeline/process/export_splitting.py \
	pipeline/sources/museums/nha/mapper.py \
	pipeline/sources/museums/nha/c359/__init__.py \
	pipeline/sources/museums/nha/c359/fetcher.py \
	pipeline/sources/museums/nha/c359/loader.py \
	pipeline/sources/museums/nha/c359/mapper.py \
	pipeline/sources/museums/nha/c1477/mapper.py \
	pipeline/sources/museums/nha/c480/mapper.py \
	pipeline/sources/museums/nha/c587/mapper.py \
	tests/test_nha_pipeline.py

SYNC_DIRS :=

.PHONY: help dry-run sync sync-files sync-dirs

help:
	@echo "Usage:"
	@echo "  make dry-run              Show files and dirs that would be copied"
	@echo "  make sync                 Copy listed files and dirs to $(LUX_WORKDIR)"
	@echo "  make sync LUX_WORKDIR=/path/to/workdir"

dry-run:
	@echo "Target: $(LUX_WORKDIR)"
	@for path in $(SYNC_FILES); do \
		echo "file $$path -> $(LUX_WORKDIR)/$$path"; \
	done
	@for path in $(SYNC_DIRS); do \
		echo "dir  $$path -> $(LUX_WORKDIR)/$$path"; \
	done

sync: sync-files sync-dirs

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
