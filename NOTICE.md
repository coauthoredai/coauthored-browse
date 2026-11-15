# Notice

Coauthored is an open preprint server for papers with AI co-authors. This repository is a
fork of arXiv's open-source **arxiv-browse**, adapted by the Coauthored contributors. It is
not affiliated with or endorsed by arXiv.

## Upstream software (MIT License)

| Upstream | Commit | How it is used |
|---|---|---|
| [arXiv/arxiv-browse](https://github.com/arXiv/arxiv-browse) | `6413996a745772c3f5e0403d99d1e774da112be1` (develop, 2026-11-12) | Forked: this repository, with its full history. |
| [arXiv/arxiv-base](https://github.com/arXiv/arxiv-base) | `8841f53ba87e1cc4694a7d9e35d6fa5dd0bb240b` (pinned in `uv.lock`) | Used unmodified as a dependency. |
| [arXiv/design-system](https://github.com/arXiv/design-system) | not included | Removed. `browse/brand.py` and `browse/templates/coauthored_brand/` were written for Coauthored and keep the same template variable names so the pages work unchanged; no design-system code, logo or stylesheet is included. |

Both upstream repositories are licensed under the MIT License, Copyright (c) 2026 arXiv, Inc.
The full licence text, with that notice and ours, is in [`LICENSE`](LICENSE). Changes made by
the Coauthored contributors are released under the same licence.

## Trademarks

"arXiv" and the arXiv logo are trademarks of arXiv and Cornell University. The MIT License
covers the code, not the name or logo, and arXiv's brand guidelines forbid names that imply an
official connection. This fork therefore:

- uses its own name, logo, colours and icons;
- removes arXiv's logos, Cornell and partner marks, and arXiv's funder and member
  acknowledgements (which are not true of Coauthored);
- links only to Coauthored's own services, never to arXiv's as if they were its own;
- identifies papers as `coauthored:YYMM.NNNNN`, never as `arXiv:` identifiers, and cites
  them with `archivePrefix={coauthored}`;
- mentions arXiv only to credit its code, in the footer and in this file.

`tests/test_coauthored_brand.py` audits the rendered pages for arXiv's name, links and colour.
