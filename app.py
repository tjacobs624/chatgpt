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

RAW_TEMPLATE = '''<!doctype html>
<title>Caddyfile Editor</title>
<style>
textarea { width: 100%; height: 80vh; font-family: monospace; }
.flash.error { color: red; }
.flash.success { color: green; }
</style>
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
<textarea name="content">{{ content }}</textarea>
<br>
<button type="submit">Save</button>
</form>'''

MANAGE_TEMPLATE = '''<!doctype html>
<title>Manage Proxies</title>
<style>
input.domain { width: 40%; }
input.proxy { width: 50%; }
.flash.error { color: red; }
.flash.success { color: green; }
</style>
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
  <button type="submit">Save</button>
</form>'''

SERVICE_TEMPLATE = '''<!doctype html>
<title>Caddy Service</title>
<style>
.flash.error { color: red; }
.flash.success { color: green; }
</style>
{% with messages = get_flashed_messages(with_categories=true) %}
  {% if messages %}
    <ul class=flashes>
    {% for category, message in messages %}
      <li class="flash {{ category }}">{{ message }}</li>
    {% endfor %}
    </ul>
  {% endif %}
{% endwith %}
<p>Status: {{ status }}</p>
<form method="get">
  <button name="action" value="start">Start</button>
  <button name="action" value="restart">Restart</button>
  <button name="action" value="stop">Stop</button>
</form>'''

HOME_TEMPLATE = '''<!doctype html>
<title>Caddy Manager</title>
<ul>
  <li><a href="{{ url_for('manage') }}">Manage Proxies</a></li>
  <li><a href="{{ url_for('raw_edit') }}">Raw Caddyfile Editor</a></li>
  <li><a href="{{ url_for('service') }}">Caddy Service</a></li>
</ul>'''

if __name__ == '__main__':
    # Listen on port 5050 so the UI is accessible via http://localhost:5050
    app.run(host='0.0.0.0', port=5050, debug=True)
