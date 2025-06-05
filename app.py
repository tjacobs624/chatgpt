from flask import Flask, render_template_string, request, redirect, url_for, flash
import subprocess

import os

app = Flask(__name__)
app.secret_key = 'change-me'

CADDYFILE_PATH = os.environ.get('CADDYFILE_PATH', '/etc/caddy/Caddyfile')

def caddy_status():
    try:
        subprocess.check_call(['systemctl', 'is-active', '--quiet', 'caddy'])
        return 'active'
    except subprocess.CalledProcessError:
        return 'inactive'

@app.route('/')
def home():
    return render_template_string(HOME_TEMPLATE)

@app.route('/raw', methods=['GET'])
def raw_edit():

    try:
        with open(CADDYFILE_PATH, 'r') as f:
            content = f.read()
    except FileNotFoundError:
        content = ''
        flash(f"Caddyfile not found at {CADDYFILE_PATH}", 'error')
    return render_template_string(RAW_TEMPLATE, content=content)

def parse_entries(text: str):
    entries = []
    lines = iter(text.splitlines())
    for line in lines:
        stripped = line.strip()
        if not stripped or stripped.startswith('#'):
            continue
        if stripped.endswith('{'):
            domain = stripped[:-1].strip()
            proxy = ''
            for inner in lines:
                s = inner.strip()
                if s.startswith('reverse_proxy'):
                    proxy = s[len('reverse_proxy'):].strip()
                if s == '}':
                    break
            if domain and proxy:
                entries.append({'domain': domain, 'proxy': proxy})
    return entries

def serialize_entries(entries):
    blocks = []
    for e in entries:
        blocks.append(f"{e['domain']} {{\n    reverse_proxy {e['proxy']}\n}}")
    return "\n\n".join(blocks) + "\n"

@app.route('/manage', methods=['GET'])
def manage():
    try:
        with open(CADDYFILE_PATH, 'r') as f:
            content = f.read()
    except FileNotFoundError:
        content = ''
        flash(f"Caddyfile not found at {CADDYFILE_PATH}", 'error')
    entries = parse_entries(content)
    return render_template_string(MANAGE_TEMPLATE, entries=entries)

@app.route('/save_entries', methods=['POST'])
def save_entries():
    domains = request.form.getlist('domain')
    proxies = request.form.getlist('proxy')
    entries = [
        {'domain': d.strip(), 'proxy': p.strip()}
        for d, p in zip(domains, proxies)
        if d.strip() and p.strip()
    ]
    content = serialize_entries(entries)
    try:
        with open(CADDYFILE_PATH, 'w') as f:
            f.write(content)
        flash('Entries saved successfully.', 'success')
    except IOError as e:
        flash(f'Error saving file: {e}', 'error')
    return redirect(url_for('manage'))

@app.route('/service', methods=['GET'])
def service():
    action = request.args.get('action')
    if action in {'start', 'stop', 'restart'}:
        try:
            subprocess.check_call(['systemctl', action, 'caddy'])
            flash(f'Caddy {action}ed successfully.', 'success')
        except subprocess.CalledProcessError as e:
            flash(f'Failed to {action} caddy: {e}', 'error')
        return redirect(url_for('service'))
    status = caddy_status()
    return render_template_string(SERVICE_TEMPLATE, status=status)


@app.route('/save', methods=['POST'])
def save():
    content = request.form.get('content', '')
    try:
        with open(CADDYFILE_PATH, 'w') as f:
            f.write(content)
        flash('Caddyfile saved successfully.', 'success')
    except IOError as e:
        flash(f'Error saving file: {e}', 'error')
    return redirect(url_for('raw_edit'))

# ...existing code...

RAW_TEMPLATE = '''<!doctype html>
<html>
<head>
<title>Caddyfile Editor</title>
<style>
body {
    background: #181c20;
    color: #e0e6ed;
    font-family: 'Segoe UI', 'Roboto', Arial, sans-serif;
    margin: 0;
    padding: 0;
}
header {
    background: #23272b;
    padding: 1.5rem 2rem;
    text-align: center;
    font-size: 2rem;
    letter-spacing: 2px;
    color: #7ec699;
    box-shadow: 0 2px 8px #0004;
}
.container {
    max-width: 900px;
    margin: 2rem auto;
    background: #23272b;
    border-radius: 12px;
    box-shadow: 0 4px 24px #0006;
    padding: 2rem 2.5rem 2.5rem 2.5rem;
}
textarea {
    width: 100%;
    height: 70vh;
    font-family: 'Fira Mono', 'Consolas', monospace;
    font-size: 1.1rem;
    background: #181c20;
    color: #e0e6ed;
    border: 1.5px solid #444;
    border-radius: 8px;
    padding: 1rem;
    margin-bottom: 1.5rem;
    transition: border 0.2s;
}
textarea:focus {
    border: 1.5px solid #7ec699;
    outline: none;
}
button {
    background: linear-gradient(90deg, #7ec699 0%, #4ecca3 100%);
    color: #181c20;
    border: none;
    border-radius: 6px;
    padding: 0.7rem 2.2rem;
    font-size: 1.1rem;
    font-weight: bold;
    cursor: pointer;
    box-shadow: 0 2px 8px #0003;
    transition: background 0.2s, color 0.2s;
}
button:hover {
    background: linear-gradient(90deg, #4ecca3 0%, #7ec699 100%);
    color: #fff;
}
ul.flashes {
    list-style: none;
    padding: 0;
    margin-bottom: 1.5rem;
}
.flash.error {
    background: #ff4e4e22;
    color: #ff6b6b;
    border-left: 4px solid #ff6b6b;
    padding: 0.7rem 1rem;
    margin-bottom: 0.5rem;
    border-radius: 6px;
}
.flash.success {
    background: #7ec69922;
    color: #7ec699;
    border-left: 4px solid #7ec699;
    padding: 0.7rem 1rem;
    margin-bottom: 0.5rem;
    border-radius: 6px;
}
@media (max-width: 600px) {
    .container { padding: 1rem; }
    textarea { height: 40vh; }
}
</style>
</head>
<body>
<header>Caddyfile Editor</header>
<div class="container">
{% with messages = get_flashed_messages(with_categories=true) %}
  {% if messages %}
    <ul class=flashes>
    {% for category, message in messages %}
      <li class="flash {{ category }}">{{ message }}</li>
    {% endfor %}
    </ul>
  {% endif %}
{% endwith %}
<form method="post" action="{{ url_for('save') }}">
<textarea name="content" spellcheck="false">{{ content }}</textarea>
<br>
<button type="submit">💾 Save</button>
</form>
</div>
</body>
</html>
'''

MANAGE_TEMPLATE = '''<!doctype html>
<html>
<head>
<title>Manage Proxies</title>
<style>
body {
    background: #181c20;
    color: #e0e6ed;
    font-family: 'Segoe UI', 'Roboto', Arial, sans-serif;
    margin: 0;
    padding: 0;
}
header {
    background: #23272b;
    padding: 1.5rem 2rem;
    text-align: center;
    font-size: 2rem;
    letter-spacing: 2px;
    color: #7ec699;
    box-shadow: 0 2px 8px #0004;
}
.container {
    max-width: 900px;
    margin: 2rem auto;
    background: #23272b;
    border-radius: 12px;
    box-shadow: 0 4px 24px #0006;
    padding: 2rem 2.5rem 2.5rem 2.5rem;
}
table#entries {
    width: 100%;
    border-collapse: collapse;
    margin-bottom: 1.5rem;
    background: #181c20;
    border-radius: 8px;
    overflow: hidden;
}
table#entries th, table#entries td {
    padding: 0.8rem 0.5rem;
    text-align: left;
}
table#entries th {
    background: #23272b;
    color: #7ec699;
    font-size: 1.1rem;
    border-bottom: 2px solid #444;
}
table#entries tr:nth-child(even) td {
    background: #23272b44;
}
input.domain, input.proxy {
    width: 95%;
    padding: 0.5rem 0.7rem;
    border: 1.5px solid #444;
    border-radius: 6px;
    background: #181c20;
    color: #e0e6ed;
    font-size: 1rem;
    transition: border 0.2s;
}
input.domain:focus, input.proxy:focus {
    border: 1.5px solid #7ec699;
    outline: none;
}
button {
    background: linear-gradient(90deg, #7ec699 0%, #4ecca3 100%);
    color: #181c20;
    border: none;
    border-radius: 6px;
    padding: 0.7rem 2.2rem;
    font-size: 1.1rem;
    font-weight: bold;
    cursor: pointer;
    box-shadow: 0 2px 8px #0003;
    transition: background 0.2s, color 0.2s;
}
button:hover {
    background: linear-gradient(90deg, #4ecca3 0%, #7ec699 100%);
    color: #fff;
}
ul.flashes {
    list-style: none;
    padding: 0;
    margin-bottom: 1.5rem;
}
.flash.error {
    background: #ff4e4e22;
    color: #ff6b6b;
    border-left: 4px solid #ff6b6b;
    padding: 0.7rem 1rem;
    margin-bottom: 0.5rem;
    border-radius: 6px;
}
.flash.success {
    background: #7ec69922;
    color: #7ec699;
    border-left: 4px solid #7ec699;
    padding: 0.7rem 1rem;
    margin-bottom: 0.5rem;
    border-radius: 6px;
}
@media (max-width: 600px) {
    .container { padding: 1rem; }
    table#entries th, table#entries td { font-size: 0.95rem; }
}
</style>
</head>
<body>
<header>Manage Proxies</header>
<div class="container">
{% with messages = get_flashed_messages(with_categories=true) %}
  {% if messages %}
    <ul class=flashes>
    {% for category, message in messages %}
      <li class="flash {{ category }}">{{ message }}</li>
    {% endfor %}
    </ul>
  {% endif %}
{% endwith %}
<form method="post" action="{{ url_for('save_entries') }}">
  <table id="entries">
    <tr><th>Domain</th><th>Proxy</th></tr>
    {% for e in entries %}
    <tr>
      <td><input name="domain" value="{{ e.domain }}" class="domain"></td>
      <td><input name="proxy" value="{{ e.proxy }}" class="proxy"></td>
    </tr>
    {% endfor %}
    <tr>
      <td><input name="domain" class="domain"></td>
      <td><input name="proxy" class="proxy"></td>
    </tr>
  </table>
  <button type="submit">💾 Save</button>
</form>
</div>
</body>
</html>
'''

SERVICE_TEMPLATE = '''<!doctype html>
<html>
<head>
<title>Caddy Service</title>
<style>
body {
    background: #181c20;
    color: #e0e6ed;
    font-family: 'Segoe UI', 'Roboto', Arial, sans-serif;
    margin: 0;
    padding: 0;
}
header {
    background: #23272b;
    padding: 1.5rem 2rem;
    text-align: center;
    font-size: 2rem;
    letter-spacing: 2px;
    color: #7ec699;
    box-shadow: 0 2px 8px #0004;
}
.container {
    max-width: 600px;
    margin: 2rem auto;
    background: #23272b;
    border-radius: 12px;
    box-shadow: 0 4px 24px #0006;
    padding: 2rem 2.5rem 2.5rem 2.5rem;
    text-align: center;
}
.status {
    font-size: 1.3rem;
    margin-bottom: 1.5rem;
    color: #7ec699;
}
button {
    background: linear-gradient(90deg, #7ec699 0%, #4ecca3 100%);
    color: #181c20;
    border: none;
    border-radius: 6px;
    padding: 0.7rem 2.2rem;
    font-size: 1.1rem;
    font-weight: bold;
    cursor: pointer;
    margin: 0 0.5rem;
    box-shadow: 0 2px 8px #0003;
    transition: background 0.2s, color 0.2s;
}
button:hover {
    background: linear-gradient(90deg, #4ecca3 0%, #7ec699 100%);
    color: #fff;
}
ul.flashes {
    list-style: none;
    padding: 0;
    margin-bottom: 1.5rem;
}
.flash.error {
    background: #ff4e4e22;
    color: #ff6b6b;
    border-left: 4px solid #ff6b6b;
    padding: 0.7rem 1rem;
    margin-bottom: 0.5rem;
    border-radius: 6px;
}
.flash.success {
    background: #7ec69922;
    color: #7ec699;
    border-left: 4px solid #7ec699;
    padding: 0.7rem 1rem;
    margin-bottom: 0.5rem;
    border-radius: 6px;
}
@media (max-width: 600px) {
    .container { padding: 1rem; }
    button { width: 100%; margin: 0.5rem 0; }
}
</style>
</head>
<body>
<header>Caddy Service</header>
<div class="container">
{% with messages = get_flashed_messages(with_categories=true) %}
  {% if messages %}
    <ul class=flashes>
    {% for category, message in messages %}
      <li class="flash {{ category }}">{{ message }}</li>
    {% endfor %}
    </ul>
  {% endif %}
{% endwith %}
<div class="status">Status: <b>{{ status }}</b></div>
<form method="get">
  <button name="action" value="start">Start</button>
  <button name="action" value="restart">Restart</button>
  <button name="action" value="stop">Stop</button>
</form>
</div>
</body>
</html>
'''

HOME_TEMPLATE = '''<!doctype html>
<html>
<head>
<title>Caddy Manager</title>
<style>
body {
    background: #181c20;
    color: #e0e6ed;
    font-family: 'Segoe UI', 'Roboto', Arial, sans-serif;
    margin: 0;
    padding: 0;
}
header {
    background: #23272b;
    padding: 2rem 2rem 1rem 2rem;
    text-align: center;
    font-size: 2.3rem;
    letter-spacing: 2px;
    color: #7ec699;
    box-shadow: 0 2px 8px #0004;
}
.container {
    max-width: 600px;
    margin: 3rem auto;
    background: #23272b;
    border-radius: 12px;
    box-shadow: 0 4px 24px #0006;
    padding: 2.5rem 2.5rem 2.5rem 2.5rem;
    text-align: center;
}
ul {
    list-style: none;
    padding: 0;
    margin: 2rem 0 0 0;
}
li {
    margin: 1.5rem 0;
}
a {
    color: #7ec699;
    text-decoration: none;
    font-size: 1.3rem;
    font-weight: bold;
    background: #181c20;
    padding: 1rem 2.5rem;
    border-radius: 8px;
    box-shadow: 0 2px 8px #0003;
    transition: background 0.2s, color 0.2s;
    display: inline-block;
}
a:hover {
    background: #7ec699;
    color: #181c20;
}
@media (max-width: 600px) {
    .container { padding: 1rem; }
    a { font-size: 1.1rem; padding: 0.7rem 1.2rem; }
}
</style>
</head>
<body>
<header>Caddy Manager</header>
<div class="container">
<ul>
  <li><a href="{{ url_for('manage') }}">Manage Proxies</a></li>
  <li><a href="{{ url_for('raw_edit') }}">Raw Caddyfile Editor</a></li>
  <li><a href="{{ url_for('service') }}">Caddy Service</a></li>
</ul>
</div>
</body>
</html>
'''


if __name__ == '__main__':
    # Listen on port 5050 so the UI is accessible via http://localhost:5050
    app.run(host='0.0.0.0', port=5050, debug=True)
