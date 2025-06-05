# Caddyfile Frontend

This repository contains a Flask application that provides a small web UI for managing your Caddyfile and controlling the Caddy service. By default it edits `/etc/caddy/Caddyfile`. You can override the path by setting the environment variable `CADDYFILE_PATH`.


## Requirements

- Python 3
- Flask

Install dependencies:

```bash
pip install -r requirements.txt
```

## Running

```bash
python app.py
```


Then open `http://localhost:5050` in your browser.

The start page links to:

- **Manage Proxies** – form based editor for `reverse_proxy` entries.
- **Raw Caddyfile Editor** – edit the file directly in a textarea.
- **Caddy Service** – view status and start/stop/restart the service.

