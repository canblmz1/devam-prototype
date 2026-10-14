"""Run the real browser checks against an isolated local prototype server."""
import os
from pathlib import Path
import socket
import subprocess
import sys
import time
from urllib.request import urlopen

root = Path(__file__).resolve().parents[1]
with socket.socket() as probe:
    probe.bind(('127.0.0.1', 0))
    port = probe.getsockname()[1]
base_url = f'http://127.0.0.1:{port}'
server = subprocess.Popen(['node', 'server.mjs', str(port)], cwd=root, stdout=subprocess.DEVNULL)
try:
    for attempt in range(100):
        if server.poll() is not None:
            raise RuntimeError('Prototype server exited before becoming ready.')
        try:
            with urlopen(base_url, timeout=1) as response:
                if response.status == 200:
                    break
        except OSError:
            time.sleep(0.1)
    else:
        raise RuntimeError('Prototype server did not become ready.')
    result = subprocess.run([sys.executable, 'tests/test-ui.py'], cwd=root,
                            env={**os.environ, 'DEVAM_TEST_URL': base_url})
    code = result.returncode
finally:
    server.terminate()
    try:
        server.wait(timeout=5)
    except subprocess.TimeoutExpired:
        server.kill()
        server.wait()
sys.exit(code)
