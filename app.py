import os
import uuid
import time
import subprocess
from flask import Flask, render_template, request, redirect, url_for, session, send_from_directory

app = Flask(__name__)
app.secret_key = 'your_secret_key_here'

UPLOAD_DIR = 'uploads'
LOG_DIR = 'logs'
os.makedirs(UPLOAD_DIR, exist_ok=True)
os.makedirs(LOG_DIR, exist_ok=True)

# Cleanup old logs (>7 days)
def cleanup_old_logs():
    now = time.time()
    for folder in [UPLOAD_DIR, LOG_DIR]:
        for filename in os.listdir(folder):
            path = os.path.join(folder, filename)
            if os.path.isfile(path) and os.stat(path).st_mtime < now - 7 * 86400:
                os.remove(path)

cleanup_old_logs()

@app.route('/')
def home():
    session['id'] = str(uuid.uuid4())
    scripts = ['disablepolicy.sh', 'mminfo.sh']  # List of available scripts
    return render_template('home.html', scripts=scripts, session_id=session['id'])

@app.route('/update_and_run', methods=['POST'])
def update_and_run():
    file_content = request.form['file_content']
    session_id = request.form['session_id']
    script = request.form['script']

    # Save uploaded file
    filename = f"{session_id}_{int(time.time())}.txt"
    filepath = os.path.join(UPLOAD_DIR, filename)
    with open(filepath, 'w') as f:
        f.write(file_content)

    # Prepare to run script
    log_file = os.path.join(LOG_DIR, f"{session_id}_{uuid.uuid4()}.log")

    # Build command
    cmd = ['./scripts/' + script]
    # If script expects an input file argument, pass it
    scripts_requiring_input = ['mminfo.sh']  # Add more scripts here if needed
    if script in scripts_requiring_input:
        cmd.append(filepath)

    # Launch script asynchronously and log output
    with open(log_file, 'w') as lf:
        subprocess.Popen(cmd, stdout=lf, stderr=lf)

    # Redirect to live log view
    return redirect(url_for('view_log', session_id=session_id, log_name=os.path.basename(log_file)))

@app.route('/logs/<session_id>/<log_name>')
def view_log(session_id, log_name):
    return render_template('log.html', session_id=session_id, log_name=log_name)

@app.route('/logs/<session_id>/<log_name>/content')
def log_content(session_id, log_name):
    log_path = os.path.join(LOG_DIR, log_name)
    if not os.path.isfile(log_path):
        return "Log not found", 404
    with open(log_path, 'r') as f:
        return f.read().replace('\n', '<br>')

@app.route('/download/<log_name>')
def download_log(log_name):
    return send_from_directory(LOG_DIR, log_name, as_attachment=True)

if __name__ == '__main__':
    app.run(host='localhost', port=5000, debug=True)

