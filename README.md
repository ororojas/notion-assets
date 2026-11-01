# notion-assets

Covers and navigation tiles for Oro's Notion workspace. Dominican blue (#002D62) and red (#CE1126) screentone on blue-black ink, with film grain.

- `covers/section-*.jpg`: the four section covers (Oro Present, Oro Future, Claude, Tomo). These carry the white cross and the one red block.
- `covers/page-*.jpg`: hub, page and project covers.
- `tiles/*.png`: arch tiles for the home-page navigation.

Everything is drawn by `tools/make_art.py`. Change a shape there and run `python3 tools/make_art.py` to regenerate.

Notion loads these through `https://raw.githubusercontent.com/ororojas/notion-assets/main/<path>`, so keep this repo public and keep file names stable.
