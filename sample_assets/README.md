# Sample Assets

Use this directory to build a small demo ZIP for local runs and smoke tests.

What is included:

- `docs/`
  - text fixtures copied from the local `texvec` repo
  - one intentional duplicate file: `galaxies-copy.md`
- `images/`
  - image fixtures copied from the local `picvec` repo
  - one intentional duplicate file: `cat1-copy.jpg`

To create a ZIP for the API:

```bash
cd sample_assets
zip -r ../sample-assets.zip .
```
