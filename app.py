from flask import Flask, render_template_string, request, redirect, url_for, flash, send_file
import subprocess
import os

app = Flask(__name__)
app.secret_key = 'your_secret_key_here'

SCRIPTS_DIR = './scripts'  # Directory where scripts are stored
LOG_FILE = 'script_output.log'
TARGET_FILE = './target_file.txt'  # File to be updated

# Homepage Template with DXC Technology logo and white header
HTML_TEMPLATE = """
<!doctype html>
<html lang="en">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>DXC Script Executor Portal</title>
    <link href="https://cdn.jsdelivr.net/npm/bootstrap@5.3.0/dist/css/bootstrap.min.css" rel="stylesheet">
    <style>
        .navbar-custom {
            background-color: #ffffff;
            border-bottom: 2px solid #ccc;
        }
    </style>
</head>
<body class="bg-light">
<nav class="navbar navbar-light navbar-custom mb-4 p-2">
  <div class="container-fluid">
    <a class="navbar-brand" href="#">
      <img src="https://dxc.com/content/dam/dxc/projects/dxc-com/us/images/about-us/newsroom/logos-for-media/vertical/DXC%20Logo_Purple+Black%20RGB.png" alt="DXC Technology" height="50">
    </a>
  </div>
</nav>
<div class="container mt-3">
    {% with messages = get_flashed_messages() %}
      {% if messages %}
        <div class="alert alert-info text-center">{{ messages[0] }}</div>
      {% endif %}
    {% endwith %}

    <div class="card shadow p-4 mb-4">
        <h2 class="mb-4 text-center">Script Executor Portal</h2>
        <form action="/run" method="post">
            <div class="mb-3">
                <label for="script" class="form-label">Choose a script:</label>
                <select name="script" id="script" class="form-select" onchange="toggleUpdateSection(this.value);" required>
                    <option value="">Select a script</option>
                    {% for script in scripts %}
                        <option value="{{ script }}">{{ script }}</option>
                    {% endfor %}
                </select>
            </div>
            <button type="submit" class="btn btn-primary w-100">Run Selected Script</button>
        </form>
        <div class="mt-4 text-center">
            <a href="/logs" class="btn btn-outline-secondary">View Logs (Auto-refresh)</a>
        </div>
    </div>

    <div class="card shadow p-4" id="updateSection" style="display:none;">
        <h2 class="mb-4 text-center">Update a File</h2>
        <p>Enter data in the format: <code>&lt;policy_name&gt; &lt;master_gpn&gt;</code></p>
        <form action="/update_file" method="post">
            <div class="mb-3">
                <label class="form-label">Enter text to update:</label>
                <textarea name="file_content" class="form-control" rows="5" required></textarea>
            </div>
            <button type="submit" class="btn btn-success w-100">Update File</button>
        </form>
    </div>
</div>

<script>
function toggleUpdateSection(script) {
    const updateSection = document.getElementById('updateSection');
    if (script === 'disablepolicy.sh') {
        updateSection.style.display = 'block';
    } else {
        updateSection.style.display = 'none';
    }
}
</script>
</body>
</html>
"""

# Logs Template with white header
LOG_TEMPLATE = """
<!doctype html>
<html lang="en">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1">
    <title>Live Script Logs</title>
    <link href="https://cdn.jsdelivr.net/npm/bootstrap@5.3.0/dist/css/bootstrap.min.css" rel="stylesheet">
    <style>
        .navbar-custom {
            background-color: #ffffff;
            border-bottom: 2px solid #ccc;
        }
        #live_log {
            height: 500px;
            overflow-y: scroll;
            background: #212529;
            color: #00FF00;
            padding: 15px;
            border-radius: 5px;
            font-family: monospace;
        }
    </style>
</head>
<body class="bg-light">
<nav class="navbar navbar-light navbar-custom mb-4 p-2">
  <div class="container-fluid">
    <a class="navbar-brand" href="#">
      <img src="https://dxc.com/content/dam/dxc/projects/dxc-com/us/images/about-us/newsroom/logos-for-media/vertical/DXC%20Logo_Purple+Black%20RGB.png" alt="DXC Technology" height="50">
    </a>
  </div>
</nav>
<div class="container mt-4">
    <div class="card shadow p-4">
        <h2 class="text-center mb-4">Live Script Output</h2>
        <p class="text-muted text-center">Refreshing every 2 seconds...</p>
        <pre id="live_log">{{ log_content }}</pre>
        <div class="text-center mt-4">
            <a href="/download_log" class="btn btn-success me-2">Download Log File</a>
            <a href="/" class="btn btn-primary">Back to Home</a>
        </div>
    </div>
</div>
<script>
    setInterval(function() {
        fetch('/logs/live')
            .then(response => response.text())
            .then(data => {
                document.getElementById('live_log').innerHTML = data;
                document.getElementById('live_log').scrollTop = document.getElementById('live_log').scrollHeight;
            });
    }, 2000);
</script>
</body>
</html>
"""

@app.route('/')
def home():
    scripts = [f for f in os.listdir(SCRIPTS_DIR) if f.endswith('.sh')]
    return render_template_string(HTML_TEMPLATE, scripts=scripts)

@app.route('/run', methods=['POST'])
def run_script():
    script_name = request.form.get('script')
    script_path = os.path.join(SCRIPTS_DIR, script_name)
    with open(LOG_FILE, 'w') as log:
        subprocess.Popen(['bash', script_path], stdout=log, stderr=log, close_fds=True)
    return redirect(url_for('logs'))

@app.route('/logs')
def logs():
    if os.path.exists(LOG_FILE):
        with open(LOG_FILE) as f:
            log_content = f.read()
    else:
        log_content = "Log file not found."
    return render_template_string(LOG_TEMPLATE, log_content=log_content)

@app.route('/logs/live')
def live_logs():
    if os.path.exists(LOG_FILE):
        with open(LOG_FILE) as f:
            return f.read()
    return "Log file not found."

@app.route('/download_log')
def download_log():
    if os.path.exists(LOG_FILE):
        return send_file(LOG_FILE, as_attachment=True)
    else:
        flash('Log file not found.')
        return redirect(url_for('logs'))

@app.route('/update_file', methods=['POST'])
def update_file():
    content = request.form.get('file_content')
    try:
        with open(TARGET_FILE, 'w') as f:
            f.write(content.strip() + '\n')
        flash('File updated successfully!')
    except Exception as e:
        flash(f'Error updating file: {str(e)}')
    return redirect(url_for('home'))

if __name__ == "__main__":
    app.run(debug=True,host="0.0.0.0", port=5000)