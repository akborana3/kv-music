import psutil
import subprocess
import os
from flask import Flask

app = Flask(__name__)

@app.route('/')
def hello_world():
    running = False
    for proc in psutil.process_iter(['pid', 'name', 'cmdline']):
        if 'python' in proc.info['name'] and 'start' in proc.info['cmdline']: 
            running = True
            break
    if running:
        return 'Bot is Running...'

    subprocess.Popen(['bash', 'start'])
    return 'Bot is Now Alive'

@app.route('/alive', methods=['POST'])
def alive():
    running = False
    for proc in psutil.process_iter(['pid', 'name', 'cmdline']):
        if 'python' in proc.info['name'] and 'start' in proc.info['cmdline']: 
            running = True
            break
    if running:
        return 'Bot Already Running...'
    else:
        subprocess.Popen(['bash', 'start'])
        return 'Bot is Now Alive'

@app.route('/health')
def health_check():
    return "PragyanBot is alive", 200

@app.route('/dev', methods=['POST'])
def dev_command():
    return "@pragyan is a developer", 200

if __name__ == '__main__':
    # Auto start the bot process on boot (Render-friendly), avoid duplicate
    try:
        running = False
        for proc in psutil.process_iter(['pid', 'name', 'cmdline']):
            cmdline = " ".join(proc.info.get('cmdline') or [])
            name = (proc.info.get('name') or "").lower()
            if ('python' in name) and ('PragyanMusic' in cmdline or 'start' in cmdline):
                running = True
                break
        if not running:
            subprocess.Popen(['bash', 'start'])
    except Exception:
        pass
    app.run(host="0.0.0.0", port=int(os.environ.get("PORT", "7860")), debug=False)
