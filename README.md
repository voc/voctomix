# VOCTOMIX

`voctomix` is a video mixing software, written in python.

We support all python versions between "latest stable" and "available in
debian stable". Older python versions might work, but we don't test on
those.

## Developer Setup

```bash
uv venv --system-site-packages
uv sync
uv pip install pygobject-stubs --config-settings=config=Gtk3
```

## Current Documentation

- [Core](https://github.com/voc/voctomix/tree/voctomix2/voctocore)
- [UI](https://github.com/voc/voctomix/tree/voctomix2/voctogui)
- [Transitions](https://github.com/voc/voctomix/blob/voctomix2/README-TRANSITIONS.md)
