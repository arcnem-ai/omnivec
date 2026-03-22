# Sample Assets

This directory gives Omnivec a small real corpus for local demos.

Contents:

- `docs/`
  - text fixtures copied from the local `texvec` repo
  - one intentional duplicate copy: `galaxies-copy.md`
- `images/`
  - image fixtures copied from the local `picvec` repo
  - one intentional duplicate copy: `cat1-copy.jpg`

To build a ZIP for the API:

```bash
cd sample_assets
zip -r ../sample-assets.zip .
```
