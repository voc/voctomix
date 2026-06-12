# VOCTOMIX

`voctomix` is a video mixing software, written in python.

We support all python versions between "latest stable" and "available in
debian stable". Older python versions might work, but we don't test on
those.

## Developer Setup

```bash
uv venv --system-site-packages
uv pip install pygobject-stubs --config-settings=config=Gtk3,Gdk3
uv sync --dev
```

## Tests

```bash
uv run pytest
uv run mypy -p voctocore -p voctogui
```

