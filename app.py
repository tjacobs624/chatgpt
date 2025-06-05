from flask import Flask, render_template_string, request, redirect, url_for, flash
import os

app = Flask(__name__)
app.secret_key = 'change-me'

CADDYFILE_PATH = os.environ.get('CADDYFILE_PATH', '/etc/caddy/Caddyfile')

@app.route('/', methods=['GET'])
def index():
    try:
        with open(CADDYFILE_PATH, 'r') as f:
            content = f.read()
    except FileNotFoundError:
        content = ''
        flash(f"Caddyfile not found at {CADDYFILE_PATH}", 'error')
    return render_template_string(TEMPLATE, content=content)

@app.route('/save', methods=['POST'])
def save():
    content = request.form.get('content', '')
    try:
        with open(CADDYFILE_PATH, 'w') as f:
            f.write(content)
        flash('Caddyfile saved successfully.', 'success')
    except IOError as e:
        flash(f'Error saving file: {e}', 'error')
    return redirect(url_for('index'))

TEMPLATE = '''<!doctype html>
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

if __name__ == '__main__':
    app.run(host='0.0.0.0', port=5000, debug=True)
