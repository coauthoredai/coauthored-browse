# coauthored-browse

The public pages of **Coauthored**, an open preprint server for papers with AI co-authors:
abstract pages, listings and PDF downloads. Every paper has at least one human author who takes
responsibility for it; AI systems are credited as authors, with their model, version and
contribution.

This is a fork of arXiv's open-source [arxiv-browse](https://github.com/arXiv/arxiv-browse)
(MIT). Coauthored is not affiliated with or endorsed by arXiv. See [`NOTICE.md`](NOTICE.md) for
what was taken from upstream, what was removed, and how arXiv's trademarks are respected.

Status: early development. The site chrome, hosts, citations and canonical links are
Coauthored's. Page templates still carry upstream text that is being rewritten; the brand
audit lists what remains:

    uv run pytest tests/test_coauthored_brand.py -s

## Run locally

With the minimal test data in this repository (Python 3.11, [uv](https://docs.astral.sh/uv/)):

    uv sync
    uv run python main.py
    # http://127.0.0.1:8080/abs/0906.5132

## Tests

    uv run pytest tests

## Configuration

`browse/config.py` defaults every host to `coauthored.pub`; set `BASE_SERVER` (and, if they
differ, `AUTH_SERVER`, `SUBMIT_SERVER`, `HELP_SERVER`, `MAIN_SERVER`) to change it. Document
storage paths (`ABS_PATH_ROOT`, `DOCUMENT_CACHE_PATH`, `DOCUMENT_LISTING_PATH`) and the database
(`CLASSIC_DB_URI`) work as in upstream.

## Licence

MIT; see [`LICENSE`](LICENSE). Copyright (c) 2026 arXiv, Inc., and portions Copyright (c) 2026
Coauthored contributors.
