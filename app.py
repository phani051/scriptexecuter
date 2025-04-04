from flask import Flask, render_template, request, redirect, url_for, flash, send_file
import subprocess
import os
import uuid
import time
import glob

app = Flask(__name__)
app.secret_key = 'your_secret_key_here'

SCRIPTS_DIR = './scripts'
LOGS_DIR = './logs'
TARGETS_DIR = './targets'
os.makedirs(LOGS_DIR, exist_ok=True)
os.makedirs(TARGETS_DIR, exist_ok=True)

def clean_old_logs():
    now = time.time()
    for f in glob.glob(os.path.join(LOGS_DIR, "*.log")):
        if os.stat(f).st_mtime < now - 7 * 86400:
            os.remove(f)
    for f in glob.glob(os.path.join(TARGETS_DIR, "*.txt")):
        if os.stat(f).st_mtime < now - 7 * 86400:
            os.remove(f)

@app.route('/')
def home():
    session_id = str(uuid.uuid4())
    scripts = [f for f in os.listdir(SCRIPTS_DIR) ]
    return render_template('home.html', scripts=scripts, session_id=session_id)

@app.route('/run', methods=['POST'])
def run_script():
    script_name = request.form.get('script')
    session_id = request.form.get('session_id')

    if not script_name:
        flash("Please select a script.")
        return redirect(url_for('home'))

    if script_name == 'disablepolicy.sh':
        flash("Please update file content below.")
        return render_template('home.html', scripts=[script_name], selected_script=script_name, session_id=session_id)

    log_file = os.path.join(LOGS_DIR, f"log_{session_id}.log")
    script_path = os.path.join(SCRIPTS_DIR, script_name)
    with open(log_file, 'w') as log:
        subprocess.Popen(['bash', script_path], stdout=log, stderr=log, close_fds=True)
    return redirect(url_for('logs', log=f"log_{session_id}.log"))

@app.route('/update_file', methods=['POST'])
def update_file():
    content = request.form.get('file_content')
    session_id = request.form.get('session_id')
    target_file = os.path.join(TARGETS_DIR, f"target_{session_id}.txt")

    try:
        with open(target_file, 'w') as f:
            f.write(content.strip() + '\n')

        script_path = os.path.join(SCRIPTS_DIR, 'disablepolicy.sh')
        log_file = os.path.join(LOGS_DIR, f"log_{session_id}.log")

        with open(log_file, 'w') as log:
            subprocess.Popen(['bash', script_path, target_file], stdout=log, stderr=log, close_fds=True)

        flash("File updated and script started.")
        return redirect(url_for('logs', log=f"log_{session_id}.log"))
    except Exception as e:
        flash(f"Error: {str(e)}")
        return redirect(url_for('home'))

@app.route('/logs')
def logs():
    log_file = request.args.get('log')
    return render_template('logs.html', log_file=log_file)

@app.route('/logs/live')
def live_logs():
    log_file = request.args.get('log')
    if log_file and os.path.exists(os.path.join(LOGS_DIR, log_file)):
        with open(os.path.join(LOGS_DIR, log_file)) as f:
            return f.read()
    return "Log not found."

@app.route('/download_log')
def download_log():
    log_file = request.args.get('log')
    full_path = os.path.join(LOGS_DIR, log_file)
    if log_file and os.path.exists(full_path):
        return send_file(full_path, as_attachment=True)
    else:
        flash('Log not found.')
        return redirect(url_for('home'))

if __name__ == "__main__":
    clean_old_logs()
    app.run(debug=True, host="135.147.56.254", port=5000)

