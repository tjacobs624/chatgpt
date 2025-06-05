# Caddyfile Frontend

This repository contains a simple Flask application to manage your Caddyfile. By default it edits `/etc/caddy/Caddyfile`. You can override the path by setting the environment variable `CADDYFILE_PATH`.

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

Then open `http://localhost:5000` in your browser.
