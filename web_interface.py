#!/usr/bin/env python3
from flask import Flask, render_template, request, jsonify, Response
import subprocess
import json
import sys
import os
import time
import threading
from pathlib import Path
from queue import Queue

app = Flask(__name__)

# Global dictionary to store investigation sessions
investigation_sessions = {}

@app.route('/')
def index():
    return '''
    <!DOCTYPE html>
    <html>
    <head>
        <title>OSINT MATRIX // PHONE INVESTIGATION TERMINAL</title>
        <link href="https://fonts.googleapis.com/css2?family=Courier+Prime:wght@400;700&display=swap" rel="stylesheet">
        <style>
            * {
                margin: 0;
                padding: 0;
                box-sizing: border-box;
            }

            body {
                background: #000;
                color: #00ff00;
                font-family: 'Courier Prime', monospace;
                overflow-x: hidden;
                min-height: 100vh;
                position: relative;
            }

            /* Matrix rain effect */
            .matrix-bg {
                position: fixed;
                top: 0;
                left: 0;
                width: 100%;
                height: 100%;
                pointer-events: none;
                z-index: -1;
                opacity: 0.1;
            }

            .terminal-container {
                max-width: 1200px;
                margin: 0 auto;
                padding: 20px;
                position: relative;
                z-index: 1;
            }

            .terminal-header {
                text-align: center;
                margin-bottom: 30px;
                border: 2px solid #00ff00;
                padding: 20px;
                background: rgba(0, 255, 0, 0.05);
                box-shadow: 0 0 20px rgba(0, 255, 0, 0.3);
            }

            .terminal-title {
                font-size: 24px;
                font-weight: bold;
                text-shadow: 0 0 10px #00ff00;
                margin-bottom: 10px;
                letter-spacing: 2px;
            }

            .terminal-subtitle {
                font-size: 14px;
                opacity: 0.8;
                letter-spacing: 1px;
            }

            .input-section {
                display: flex;
                align-items: center;
                justify-content: center;
                margin-bottom: 30px;
                gap: 15px;
            }

            .phone-input {
                background: #000;
                border: 2px solid #00ff00;
                color: #00ff00;
                padding: 15px 20px;
                font-family: 'Courier Prime', monospace;
                font-size: 16px;
                width: 300px;
                text-align: center;
                box-shadow: inset 0 0 10px rgba(0, 255, 0, 0.2);
                transition: all 0.3s ease;
            }

            .phone-input:focus {
                outline: none;
                box-shadow: 0 0 20px rgba(0, 255, 0, 0.5);
                text-shadow: 0 0 5px #00ff00;
            }

            .hack-button {
                background: #000;
                border: 2px solid #00ff00;
                color: #00ff00;
                padding: 15px 30px;
                font-family: 'Courier Prime', monospace;
                font-size: 16px;
                font-weight: bold;
                cursor: pointer;
                text-transform: uppercase;
                letter-spacing: 1px;
                transition: all 0.3s ease;
                position: relative;
                overflow: hidden;
            }

            .hack-button:hover {
                background: rgba(0, 255, 0, 0.1);
                box-shadow: 0 0 20px rgba(0, 255, 0, 0.5);
                text-shadow: 0 0 10px #00ff00;
            }

            .hack-button:active {
                transform: scale(0.98);
            }

            .advanced-section {
                margin-top: 20px;
                padding: 20px;
                background: rgba(0, 255, 0, 0.05);
                border: 1px solid #00ff00;
                border-radius: 5px;
                transition: all 0.3s ease;
            }

            .phone-input-container {
                background: rgba(0, 255, 0, 0.05);
                border: 1px solid rgba(0, 255, 0, 0.3);
                border-radius: 5px;
                padding: 20px;
                margin-bottom: 20px;
                text-align: center;
            }

            .advanced-toggle-text {
                color: #00aa00;
                font-family: 'Courier Prime', monospace;
                font-size: 14px;
                cursor: pointer;
                transition: all 0.3s ease;
                margin-top: 10px;
                text-decoration: underline;
                opacity: 0.8;
            }

            .advanced-toggle-text:hover {
                color: #00ff00;
                opacity: 1;
                text-shadow: 0 0 5px rgba(0, 255, 0, 0.5);
            }

            .identity-inputs {
                display: flex;
                flex-wrap: wrap;
                gap: 15px;
                justify-content: center;
                margin-top: 15px;
            }

            .identity-input {
                background: transparent;
                border: 1px solid rgba(0, 255, 0, 0.5);
                color: #00ff00;
                padding: 8px 12px;
                font-family: 'Courier Prime', monospace;
                font-size: 12px;
                border-radius: 3px;
                outline: none;
                transition: all 0.3s ease;
                width: 140px;
                text-align: center;
            }

            .identity-input:focus {
                outline: none;
                border-color: #00ff00;
                box-shadow: 0 0 10px rgba(0, 255, 0, 0.3);
            }

            .identity-input::placeholder {
                color: rgba(0, 255, 0, 0.6);
            }

            .advanced-section.hidden {
                display: none;
            }

            .terminal-output {
                background: #000;
                border: 2px solid #00ff00;
                min-height: 500px;
                padding: 20px;
                font-size: 14px;
                line-height: 1.4;
                box-shadow: inset 0 0 20px rgba(0, 255, 0, 0.1);
                position: relative;
                overflow-y: auto;
                max-height: 70vh;
            }

            .terminal-line {
                margin-bottom: 5px;
                opacity: 0;
                animation: fadeIn 0.5s ease forwards;
            }

            .terminal-prompt {
                color: #00ff00;
                text-shadow: 0 0 5px #00ff00;
            }

            .terminal-success {
                color: #00ff00;
                text-shadow: 0 0 5px #00ff00;
            }

            .terminal-error {
                color: #ff0066;
                text-shadow: 0 0 5px #ff0066;
            }

            .terminal-warning {
                color: #ffff00;
                text-shadow: 0 0 5px #ffff00;
            }

            .terminal-info {
                color: #00ccff;
                text-shadow: 0 0 5px #00ccff;
            }

            .terminal-funny {
                color: #ff00ff;
                text-shadow: 0 0 5px #ff00ff;
                font-style: italic;
            }

            .terminal-oracle {
                color: #ffaa00;
                text-shadow: 0 0 5px #ffaa00;
                font-weight: bold;
            }

            .terminal-system {
                color: #00ff88;
                text-shadow: 0 0 5px #00ff88;
            }

            .terminal-api {
                color: #88aaff;
                text-shadow: 0 0 5px #88aaff;
            }

            .terminal-intel {
                color: #ff8800;
                text-shadow: 0 0 5px #ff8800;
                font-weight: bold;
            }

            .terminal-scanning {
                color: #ffff88;
                text-shadow: 0 0 5px #ffff88;
            }

            .cursor {
                display: inline-block;
                width: 10px;
                height: 18px;
                background: #00ff00;
                animation: blink 1s infinite;
                margin-left: 2px;
            }

            @keyframes fadeIn {
                to { opacity: 1; }
            }

            @keyframes blink {
                0%, 50% { opacity: 1; }
                51%, 100% { opacity: 0; }
            }

            .glitch {
                animation: glitch 0.5s ease-in-out;
            }

            @keyframes glitch {
                0% { transform: translate(0); }
                20% { transform: translate(-2px, 2px); }
                40% { transform: translate(-2px, -2px); }
                60% { transform: translate(2px, 2px); }
                80% { transform: translate(2px, -2px); }
                100% { transform: translate(0); }
            }

            .scan-line {
                position: absolute;
                top: 0;
                left: 0;
                right: 0;
                height: 2px;
                background: linear-gradient(90deg, transparent, #00ff00, transparent);
                animation: scan 2s linear infinite;
            }

            @keyframes scan {
                0% { top: 0%; }
                100% { top: 100%; }
            }

            .matrix-text {
                font-family: 'Courier Prime', monospace;
                font-size: 12px;
                color: #00ff00;
                opacity: 0.3;
                position: absolute;
                animation: fall linear infinite;
            }

            @keyframes fall {
                0% { top: -100px; }
                100% { top: 100vh; }
            }

            .report-link {
                display: inline-block;
                margin-top: 20px;
                padding: 10px 20px;
                background: rgba(0, 255, 0, 0.1);
                border: 1px solid #00ff00;
                color: #00ff00;
                text-decoration: none;
                font-family: 'Courier Prime', monospace;
                text-transform: uppercase;
                letter-spacing: 1px;
                transition: all 0.3s ease;
            }

            .report-link:hover {
                background: rgba(0, 255, 0, 0.2);
                box-shadow: 0 0 15px rgba(0, 255, 0, 0.5);
                text-shadow: 0 0 10px #00ff00;
            }

            .report-container {
                margin-top: 20px;
                border: 2px solid #00ff00;
                background: rgba(0, 0, 0, 0.8);
                max-height: 70vh;
                overflow-y: auto;
                padding: 0;
            }

            .report-container iframe {
                width: 100%;
                height: 70vh;
                border: none;
                background: white;
            }

            .close-report {
                background: #ff0066;
                border: 1px solid #ff0066;
                color: white;
                padding: 5px 10px;
                cursor: pointer;
                float: right;
                margin: 5px;
                font-family: 'Courier Prime', monospace;
            }
        </style>
    </head>
    <body>
        <canvas class="matrix-bg" id="matrixCanvas"></canvas>

        <div class="terminal-container">
            <div class="terminal-header">
                <div class="terminal-title">◉ PHONE DEEP (SO DEEP) OSINT INVESTIGATION FRAMEWORK ◉</div>
                <div class="terminal-subtitle">It's time to consult the Oracle, Neo...</div>
            </div>

            <div class="input-section">
                <div class="phone-input-container">
                    <input type="text" class="phone-input" id="phone" placeholder="+1234567890" maxlength="15">
                    <div class="advanced-toggle-text" onclick="toggleAdvanced()">
                        🔧 Click here for enhanced identity hunting options
                    </div>
                </div>

                <div class="advanced-section hidden" id="advancedSection">
                    <div style="color: #00ff00; margin-bottom: 15px; text-align: center;">
                        🎯 ENHANCED IDENTITY HUNTING 🎯<br>
                        <small>💡 Tip: At least one additional attribute significantly improves name resolution from Twilio and other APIs</small>
                    </div>
                    <div class="identity-inputs">
                        <input type="text" class="identity-input" id="firstName" placeholder="First Name">
                        <input type="text" class="identity-input" id="lastName" placeholder="Last Name">
                        <input type="text" class="identity-input" id="city" placeholder="City">
                        <input type="text" class="identity-input" id="state" placeholder="State">
                        <input type="text" class="identity-input" id="postalCode" placeholder="ZIP Code">
                        <input type="text" class="identity-input" id="address" placeholder="Address">
                    </div>
                </div>

                <button class="hack-button" id="mainButton" onclick="initInvestigation()">
                    > Which Pill Will You Choose? <
                </button>
            </div>

            <div class="terminal-output" id="terminal">
                <div class="scan-line"></div>
                <div class="terminal-line terminal-prompt">[ORACLE] Welcome, my child. The matrix of phone numbers awaits...</div>
                <div class="terminal-line terminal-info">[SYSTEM] Deep (SO DEEP) scanning protocols loaded and ready</div>
                <div class="terminal-line terminal-warning">[WARNING] Use responsibly, young grasshopper. With great power...</div>
                <div class="terminal-line terminal-success">[MORPHEUS] Take the red pill to begin your journey into phone enlightenment</div>
                <div class="terminal-line terminal-prompt">[READY] Enter target digits to go down the rabbit hole<span class="cursor"></span></div>
            </div>
        </div>

        <script>
            // Matrix rain effect
            function initMatrix() {
                const canvas = document.getElementById('matrixCanvas');
                const ctx = canvas.getContext('2d');

                canvas.width = window.innerWidth;
                canvas.height = window.innerHeight;

                const chars = 'アィウェオカキクケコサシスセソタチツテトナニヌネノハヒフヘホマミムメモヤユヨラリルレロワヲン01234567890ABCDEFGHIJKLMNOPQRSTUVWXYZ';
                const charArray = chars.split('');

                const fontSize = 14;
                const columns = canvas.width / fontSize;
                const drops = Array.from({length: columns}, () => 1);

                function draw() {
                    ctx.fillStyle = 'rgba(0, 0, 0, 0.05)';
                    ctx.fillRect(0, 0, canvas.width, canvas.height);

                    ctx.fillStyle = '#00ff00';
                    ctx.font = fontSize + 'px monospace';

                    for (let i = 0; i < drops.length; i++) {
                        const text = charArray[Math.floor(Math.random() * charArray.length)];
                        ctx.fillText(text, i * fontSize, drops[i] * fontSize);

                        if (drops[i] * fontSize > canvas.height && Math.random() > 0.975) {
                            drops[i] = 0;
                        }
                        drops[i]++;
                    }
                }

                setInterval(draw, 33);
            }

            // Terminal functionality
            let currentSessionId = null;

            function addTerminalLine(text, type = 'prompt', color = null) {
                const terminal = document.getElementById('terminal');
                const line = document.createElement('div');

                // Use color type if provided, otherwise fall back to message type
                const colorClass = color || type;
                line.className = `terminal-line terminal-${colorClass}`;
                line.innerHTML = text;
                terminal.appendChild(line);
                terminal.scrollTop = terminal.scrollHeight;
            }

            function typeWriterEffect(element, text, callback) {
                let i = 0;
                element.innerHTML = '';
                const timer = setInterval(() => {
                    if (i < text.length) {
                        element.innerHTML += text.charAt(i);
                        i++;
                    } else {
                        clearInterval(timer);
                        if (callback) callback();
                    }
                }, 30);
            }

            function toggleAdvanced() {
                const section = document.getElementById('advancedSection');
                const button = event.target;
                const mainButton = document.getElementById('mainButton');

                if (section.classList.contains('hidden')) {
                    section.classList.remove('hidden');
                    button.textContent = '🔽 Click here to hide advanced options';
                    mainButton.textContent = '> YEET BOTH PILLS <';
                    addTerminalLine('[SYSTEM] Advanced identity hunting protocols activated', 'info');
                } else {
                    section.classList.add('hidden');
                    button.textContent = '🔧 Click here for enhanced identity hunting options';
                    mainButton.textContent = '> Which Pill Will You Choose? <';
                    addTerminalLine('[SYSTEM] Standard investigation mode selected', 'info');
                }
            }

            function collectIdentityData() {
                const identityData = {};

                const firstName = document.getElementById('firstName').value.trim();
                const lastName = document.getElementById('lastName').value.trim();
                const city = document.getElementById('city').value.trim();
                const state = document.getElementById('state').value.trim();
                const postalCode = document.getElementById('postalCode').value.trim();
                const address = document.getElementById('address').value.trim();

                if (firstName) identityData.first_name = firstName;
                if (lastName) identityData.last_name = lastName;
                if (city) identityData.city = city;
                if (state) identityData.state = state;
                if (postalCode) identityData.postal_code = postalCode;
                if (address) identityData.address = address;

                return identityData;
            }

            function initInvestigation() {
                const phone = document.getElementById('phone').value;
                if (!phone) {
                    addTerminalLine('[ERROR] No target coordinates provided', 'error');
                    return;
                }

                // Clear terminal
                document.getElementById('terminal').innerHTML = '<div class="scan-line"></div>';

                // Generate session ID
                currentSessionId = Date.now().toString();

                // Collect identity data for enhanced hunting
                const identityData = collectIdentityData();
                const hasIdentityData = Object.keys(identityData).length > 0;

                if (hasIdentityData) {
                    addTerminalLine(`[SYSTEM] Enhanced identity hunting mode activated`, 'success');
                    addTerminalLine(`[SYSTEM] Identity parameters: ${Object.keys(identityData).join(', ')}`, 'info');
                } else {
                    addTerminalLine(`[SYSTEM] Standard hunting mode - phone number only`, 'info');
                }

                addTerminalLine(`[SYSTEM] Initiating investigation for target: ${phone}`, 'success');
                addTerminalLine('[SYSTEM] Establishing secure connection...', 'info');
                addTerminalLine('[SYSTEM] Loading deep scan modules...', 'info');
                addTerminalLine('[SYSTEM] Bypassing security protocols...', 'warning');

                // Start investigation with identity data
                const payload = {
                    phone: phone,
                    session_id: currentSessionId
                };

                if (hasIdentityData) {
                    payload.identity_data = identityData;
                    addTerminalLine('[SYSTEM] Uploading identity parameters for enhanced hunting...', 'warning');
                }

                fetch('/investigate', {
                    method: 'POST',
                    headers: {'Content-Type': 'application/json'},
                    body: JSON.stringify(payload)
                })
                .then(response => {
                    if (response.ok) {
                        startStreaming(currentSessionId);
                    } else {
                        addTerminalLine('[ERROR] Failed to initialize investigation', 'error');
                    }
                })
                .catch(error => {
                    addTerminalLine(`[ERROR] Connection failed: ${error}`, 'error');
                });
            }

            function startStreaming(sessionId) {
                const eventSource = new EventSource(`/stream/${sessionId}`);

                eventSource.onmessage = function(event) {
                    const data = JSON.parse(event.data);

                    if (data.type === 'output') {
                        addTerminalLine(data.message, 'info', data.color);
                    } else if (data.type === 'error') {
                        addTerminalLine(data.message, 'error');
                    } else if (data.type === 'complete') {
                        addTerminalLine('[SYSTEM] Investigation complete. Report generated.', 'success');
                        if (data.report_url) {
                            const terminal = document.getElementById('terminal');
                            const linkDiv = document.createElement('div');
                            linkDiv.className = 'terminal-line';
                            linkDiv.innerHTML = `
                                <div style="margin-top: 15px;">
                                    <a href="${data.report_url}" target="_blank" class="report-link" style="margin-right: 15px;">>> OPEN REPORT IN NEW TAB <<</a>
                                    <button onclick="loadReportInline('${data.report_url}')" class="report-link" style="background: rgba(255,165,0,0.1); border-color: #ffaa00; color: #ffaa00;">>> VIEW REPORT HERE <<</button>
                                </div>
                            `;
                            terminal.appendChild(linkDiv);
                        }
                        eventSource.close();
                    }
                };

                eventSource.onerror = function() {
                    addTerminalLine('[ERROR] Stream connection lost', 'error');
                    eventSource.close();
                };
            }

            // Initialize matrix effect when page loads
            window.onload = function() {
                initMatrix();

                // Add glitch effect occasionally
                setInterval(() => {
                    if (Math.random() > 0.95) {
                        document.querySelector('.terminal-header').classList.add('glitch');
                        setTimeout(() => {
                            document.querySelector('.terminal-header').classList.remove('glitch');
                        }, 500);
                    }
                }, 3000);
            };

            // Handle enter key
            document.getElementById('phone').addEventListener('keypress', function(e) {
                if (e.key === 'Enter') {
                    initInvestigation();
                }
            });

            // Function to load report inline
            function loadReportInline(reportUrl) {
                // Check if report container already exists
                let reportContainer = document.getElementById('reportContainer');
                if (reportContainer) {
                    reportContainer.remove();
                }

                // Create new report container
                reportContainer = document.createElement('div');
                reportContainer.id = 'reportContainer';
                reportContainer.className = 'report-container';
                reportContainer.innerHTML = `
                    <button class="close-report" onclick="closeReport()">✕ CLOSE REPORT</button>
                    <iframe src="${reportUrl}" title="Investigation Report"></iframe>
                `;

                // Add to page
                document.querySelector('.terminal-container').appendChild(reportContainer);

                // Scroll to report
                reportContainer.scrollIntoView({ behavior: 'smooth' });
            }

            // Function to close inline report
            function closeReport() {
                const reportContainer = document.getElementById('reportContainer');
                if (reportContainer) {
                    reportContainer.remove();
                }
            }

            // Resize matrix canvas
            window.addEventListener('resize', () => {
                const canvas = document.getElementById('matrixCanvas');
                canvas.width = window.innerWidth;
                canvas.height = window.innerHeight;
            });
        </script>
    </body>
    </html>
    '''

@app.route('/investigate', methods=['POST'])
def investigate():
    phone = request.json['phone']
    session_id = request.json.get('session_id', str(time.time()))
    identity_data = request.json.get('identity_data', {})

    # Create a queue for this session
    output_queue = Queue()
    investigation_sessions[session_id] = {
        'queue': output_queue,
        'status': 'running',
        'phone': phone
    }

    # Start investigation in background thread
    def run_investigation():
        python_path = sys.executable

        try:
            # Build command with identity data
            cmd = [python_path, 'phone_osint_master.py', phone]
            if identity_data:
                cmd.append(json.dumps(identity_data))
                output_queue.put(('info', f"🎯 Enhanced investigation with identity data: {list(identity_data.keys())}"))

            # Run investigation with real-time output capture
            process = subprocess.Popen(
                cmd,
                stdout=subprocess.PIPE,
                stderr=subprocess.STDOUT,
                text=True,
                bufsize=1,
                universal_newlines=True,
                cwd=os.getcwd()
            )

            # Read output line by line
            for line in iter(process.stdout.readline, ''):
                if line:
                    # Add hacker-style formatting to output
                    formatted_line, color_type = format_matrix_output(line.strip())
                    output_queue.put({'type': 'output', 'message': formatted_line, 'color': color_type})

            process.wait()

            if process.returncode == 0:
                # Find latest report
                reports = list(Path('results').glob('*/investigation_report.html'))
                if reports:
                    latest_report = max(reports, key=lambda p: p.stat().st_mtime)
                    output_queue.put({
                        'type': 'complete',
                        'report_url': f'/report/{latest_report.parent.name}'
                    })
                else:
                    output_queue.put({
                        'type': 'error',
                        'message': '[ERROR] No report was generated'
                    })
            else:
                output_queue.put({
                    'type': 'error',
                    'message': f'[ERROR] Investigation failed with code: {process.returncode}'
                })

        except Exception as e:
            output_queue.put({
                'type': 'error',
                'message': f'[ERROR] Investigation crashed: {str(e)}'
            })
        finally:
            investigation_sessions[session_id]['status'] = 'complete'

    # Start the investigation thread
    investigation_thread = threading.Thread(target=run_investigation)
    investigation_thread.daemon = True
    investigation_thread.start()

    return jsonify({'status': 'started', 'session_id': session_id})

def format_matrix_output(line):
    """Format output lines with Matrix-style hacker aesthetic and random funny quotes"""
    import random

    line = line.strip()
    if not line:
        return line, 'info'

    # Random funny quotes to inject occasionally
    funny_quotes = [
        "[ORACLE] That's a nice coat you brought me, but your investigation skills need work.",
        "[CIPHER] Welcome to the desert of the real...phone numbers!",
        "[MORPHEUS] There is no spoon...but there is definitely a phone number.",
        "[AGENT] We know where you live...and now we know who you're investigating!",
        "[TRINITY] I'm in. The phone system has been compromised.",
        "[ORACLE] The path of the one is fraught with broken API calls.",
        "[NEO] Whoa...I know phone validation.",
    ]

    # Occasionally inject a funny quote (5% chance)
    if random.random() < 0.05:
        return random.choice(funny_quotes), 'funny'

    # Add prefixes based on content and return with color type
    if 'error' in line.lower() or 'failed' in line.lower():
        return f'[ERROR] {line}', 'error'
    elif 'warning' in line.lower():
        return f'[WARNING] {line}', 'warning'
    elif 'testing' in line.lower() or 'checking' in line.lower():
        return f'[SCANNING] {line}', 'scanning'
    elif 'complete' in line.lower() or 'success' in line.lower():
        return f'[SUCCESS] {line}', 'success'
    elif 'api' in line.lower():
        return f'[API] {line}', 'api'
    elif 'found' in line.lower() or 'located' in line.lower():
        return f'[INTEL] {line}', 'intel'
    elif 'twilio' in line.lower():
        return f'[TWILIO] {line} (that\'s some deep validation right there)', 'api'
    elif 'numverify' in line.lower():
        return f'[NUMVERIFY] {line} (getting DEEP into those digits)', 'api'
    elif 'breach' in line.lower():
        return f'[BREACH] {line} (hope they weren\'t using 123456 as password)', 'intel'
    elif line.startswith('[ORACLE]') or line.startswith('[MORPHEUS]') or line.startswith('[CIPHER]'):
        return line, 'oracle'
    elif line.startswith('[SYSTEM]'):
        return line, 'system'
    else:
        return f'[INFO] {line}', 'info'

@app.route('/stream/<session_id>')
def stream_output(session_id):
    """Stream investigation output in real-time"""
    def generate():
        if session_id not in investigation_sessions:
            yield f"data: {json.dumps({'type': 'error', 'message': '[ERROR] Invalid session'})}\n\n"
            return

        session = investigation_sessions[session_id]
        queue = session['queue']

        # Send initial funny Matrix-style messages with colors
        funny_messages = [
            ('[ORACLE] My child, the chosen one has arrived...you seek the forbidden digits?', 'oracle'),
            ('[SYSTEM] Loading underground hacker protocols...', 'system'),
            ('[CIPHER] Welcome to the real world, my Z4ddy!', 'funny'),
            ('[ORACLE] I see you are the one...but also kind of a little B!TCH! Break yourself, pasty white boy!', 'funny'),
            ('[SYSTEM] Bypassing corporate surveillance networks...', 'system'),
            ('[MORPHEUS] What if I told you...this phone number is about to get DEEP scanned?', 'oracle'),
            (f'[TARGET] Beginning deep (SO DEEP) investigation of {session["phone"]}', 'intel'),
            ('[AGENT] We are aware of your activities...proceed anyway.', 'warning'),
            ('[SYSTEM] Entering the rabbit hole... hope you brought snacks!', 'system'),
            ('[SYSTEM] ==================================', 'system')
        ]

        for msg, color_type in funny_messages:
            yield f"data: {json.dumps({'type': 'output', 'message': msg, 'color': color_type})}\n\n"
            time.sleep(0.5)

        # Stream actual output
        while True:
            try:
                # Check if investigation is still running
                if session['status'] == 'complete' and queue.empty():
                    break

                # Get message from queue (wait up to 1 second)
                try:
                    message = queue.get(timeout=1)
                    yield f"data: {json.dumps(message)}\n\n"

                    if message.get('type') == 'complete':
                        break

                except:
                    # No message available, send heartbeat
                    continue

            except Exception as e:
                yield f"data: {json.dumps({'type': 'error', 'message': f'[ERROR] Stream error: {str(e)}'})}\n\n"
                break

        # Cleanup session
        if session_id in investigation_sessions:
            del investigation_sessions[session_id]

    return Response(
        generate(),
        mimetype='text/event-stream',
        headers={
            'Cache-Control': 'no-cache',
            'Connection': 'keep-alive',
            'Access-Control-Allow-Origin': '*'
        }
    )

@app.route('/report/<report_id>')
def view_report(report_id):
    report_path = Path(f'results/{report_id}/investigation_report.html')
    return report_path.read_text()

if __name__ == '__main__':
    app.run(debug=True, port=5000)