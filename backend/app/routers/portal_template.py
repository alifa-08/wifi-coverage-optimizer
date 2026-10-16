import html
from typing import Dict, Any, Optional


def render_captive_portal_html(params: Dict[str, Any]) -> str:
    """
    Renders a modern, mobile-friendly, self-contained HTML Captive Portal.
    Uses pure embedded CSS and vanilla JavaScript with zero external CDN dependencies,
    ensuring 100% functionality on isolated captive Wi-Fi subnets without internet access.
    """
    client_mac = html.escape(params.get("clientmac") or params.get("client_mac") or "")
    client_ip = html.escape(params.get("clientip") or params.get("client_ip") or "")
    hid = html.escape(params.get("hid") or "")
    gw_addr = html.escape(params.get("gatewayaddress") or "192.168.214.2:2050")
    gw_name = html.escape(params.get("gatewayname") or "Campus OpenWrt Gateway")
    authdir = html.escape(params.get("authdir") or "opennds_auth")
    redir_url = html.escape(params.get("originurl") or params.get("redir") or "https://www.google.com")
    fas_raw = html.escape(params.get("fas") or params.get("fas_blob") or "")
    error_msg = html.escape(params.get("error_message") or "")
    success_msg = html.escape(params.get("success_message") or "")

    error_html = f"""
    <div class="alert alert-error">
        <svg class="alert-icon" fill="none" viewBox="0 0 24 24" stroke="currentColor">
            <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M12 9v2m0 4h.01m-6.938 4h13.856c1.54 0 2.502-1.667 1.732-3L13.732 4c-.77-1.333-2.694-1.333-3.464 0L3.34 16c-.77 1.333.192 3 1.732 3z"/>
        </svg>
        <div>
            <strong>Access Denied:</strong> {error_msg}
        </div>
    </div>
    """ if error_msg else ""

    success_html = f"""
    <div class="alert alert-success">
        <svg class="alert-icon" fill="none" viewBox="0 0 24 24" stroke="currentColor">
            <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M9 12l2 2 4-4m6 2a9 9 0 11-18 0 9 9 0 0118 0z"/>
        </svg>
        <div>
            <strong>Success:</strong> {success_msg}
        </div>
    </div>
    """ if success_msg else ""

    return f"""<!DOCTYPE html>
<html lang="en">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0, maximum-scale=1.0, user-scalable=no">
    <title>Campus Wi-Fi Portal | Student Authentication</title>
    <style>
        :root {{
            --primary: #1e40af;
            --primary-hover: #1d4ed8;
            --accent: #0284c7;
            --bg: #f8fafc;
            --card-bg: #ffffff;
            --text-main: #0f172a;
            --text-muted: #64748b;
            --border: #e2e8f0;
            --success: #15803d;
            --success-bg: #dcfce7;
            --danger: #b91c1c;
            --danger-bg: #fee2e2;
            --info: #0369a1;
            --info-bg: #e0f2fe;
            --radius: 12px;
        }}
        * {{
            box-sizing: border-box;
            margin: 0;
            padding: 0;
            font-family: -apple-system, BlinkMacSystemFont, "Segoe UI", Roboto, Helvetica, Arial, sans-serif;
        }}
        body {{
            background: linear-gradient(135deg, #f0fdf4 0%, #f8fafc 50%, #eff6ff 100%);
            color: var(--text-main);
            min-height: 100vh;
            display: flex;
            align-items: center;
            justify-content: center;
            padding: 16px;
        }}
        .portal-container {{
            width: 100%;
            max-width: 480px;
            background: var(--card-bg);
            border-radius: var(--radius);
            box-shadow: 0 10px 25px -5px rgba(0, 0, 0, 0.08), 0 8px 10px -6px rgba(0, 0, 0, 0.04);
            border: 1px solid var(--border);
            overflow: hidden;
        }}
        .header {{
            background: linear-gradient(135deg, #1e3a8a 0%, #1e40af 100%);
            color: #ffffff;
            padding: 24px 20px;
            text-align: center;
            position: relative;
        }}
        .header-badge {{
            display: inline-flex;
            align-items: center;
            gap: 6px;
            background: rgba(255, 255, 255, 0.15);
            padding: 4px 12px;
            border-radius: 9999px;
            font-size: 11px;
            font-weight: 600;
            text-transform: uppercase;
            letter-spacing: 0.05em;
            margin-bottom: 8px;
        }}
        .header h1 {{
            font-size: 20px;
            font-weight: 700;
            letter-spacing: -0.01em;
            margin-bottom: 4px;
        }}
        .header p {{
            font-size: 13px;
            opacity: 0.9;
        }}
        .content {{
            padding: 20px;
        }}
        .alert {{
            padding: 12px 14px;
            border-radius: 8px;
            font-size: 13px;
            margin-bottom: 16px;
            display: flex;
            align-items: flex-start;
            gap: 10px;
            line-height: 1.4;
        }}
        .alert-error {{
            background: var(--danger-bg);
            color: var(--danger);
            border: 1px solid #fca5a5;
        }}
        .alert-success {{
            background: var(--success-bg);
            color: var(--success);
            border: 1px solid #86efac;
        }}
        .alert-icon {{
            width: 18px;
            height: 18px;
            flex-shrink: 0;
            margin-top: 1px;
        }}
        .info-card {{
            background: #f8fafc;
            border: 1px solid var(--border);
            border-radius: 8px;
            padding: 12px;
            margin-bottom: 16px;
            font-size: 12px;
        }}
        .info-row {{
            display: flex;
            justify-content: space-between;
            margin-bottom: 6px;
            color: var(--text-muted);
        }}
        .info-row:last-child {{
            margin-bottom: 0;
        }}
        .info-val {{
            font-weight: 600;
            color: var(--text-main);
            font-family: ui-monospace, SFMono-Regular, Menlo, Monaco, Consolas, monospace;
        }}
        .quota-banner {{
            background: #f0fdf4;
            border: 1px solid #bbf7d0;
            color: #166534;
            border-radius: 8px;
            padding: 10px 12px;
            font-size: 12px;
            margin-bottom: 16px;
            line-height: 1.4;
        }}
        .form-group {{
            margin-bottom: 14px;
        }}
        .form-label {{
            display: block;
            font-size: 13px;
            font-weight: 600;
            color: var(--text-main);
            margin-bottom: 5px;
        }}
        .form-input {{
            width: 100%;
            padding: 10px 12px;
            border: 1px solid var(--border);
            border-radius: 8px;
            font-size: 14px;
            outline: none;
            transition: border-color 0.15s, box-shadow 0.15s;
            background: #ffffff;
        }}
        .form-input:focus {{
            border-color: var(--primary);
            box-shadow: 0 0 0 3px rgba(30, 64, 175, 0.1);
        }}
        .demo-pills {{
            display: flex;
            flex-wrap: wrap;
            gap: 6px;
            margin-top: 6px;
        }}
        .demo-pill {{
            background: #e2e8f0;
            color: #334155;
            font-size: 11px;
            font-weight: 600;
            padding: 3px 8px;
            border-radius: 4px;
            cursor: pointer;
            border: none;
            transition: background 0.15s;
        }}
        .demo-pill:hover {{
            background: #cbd5e1;
        }}
        .btn {{
            width: 100%;
            padding: 12px;
            border: none;
            border-radius: 8px;
            font-size: 15px;
            font-weight: 600;
            cursor: pointer;
            transition: all 0.15s;
            display: flex;
            align-items: center;
            justify-content: center;
            gap: 8px;
        }}
        .btn-primary {{
            background: var(--primary);
            color: #ffffff;
        }}
        .btn-primary:hover {{
            background: var(--primary-hover);
        }}
        .btn-primary:disabled {{
            background: #94a3b8;
            cursor: not-allowed;
        }}
        .otp-row {{
            display: flex;
            gap: 8px;
        }}
        .otp-btn {{
            white-space: nowrap;
            background: #f1f5f9;
            color: #0f172a;
            border: 1px solid var(--border);
            border-radius: 8px;
            font-size: 12px;
            font-weight: 600;
            padding: 0 12px;
            cursor: pointer;
            transition: background 0.15s;
        }}
        .otp-btn:hover {{
            background: #e2e8f0;
        }}
        .footer {{
            padding: 12px 20px 16px;
            text-align: center;
            font-size: 11px;
            color: var(--text-muted);
            border-top: 1px solid var(--border);
            background: #f8fafc;
        }}
        .status-badge {{
            display: inline-block;
            width: 8px;
            height: 8px;
            border-radius: 50%;
            background: #22c55e;
            margin-right: 4px;
        }}
        #progressCard {{
            display: none;
            text-align: center;
            padding: 24px 10px;
        }}
        .spinner {{
            width: 36px;
            height: 36px;
            border: 4px solid #e2e8f0;
            border-top-color: var(--primary);
            border-radius: 50%;
            animation: spin 0.8s linear infinite;
            margin: 0 auto 12px;
        }}
        @keyframes spin {{
            to {{ transform: rotate(360deg); }}
        }}
    </style>
</head>
<body>
    <div class="portal-container">
        <div class="header">
            <div class="header-badge">
                <span class="status-badge"></span> OpenWrt Gateway Active
            </div>
            <h1>Campus Wi-Fi Login</h1>
            <p>AI-Optimized Network & Quota Enforced Access</p>
        </div>

        <div class="content">
            {error_html}
            {success_html}

            <div class="info-card">
                <div class="info-row">
                    <span>Client Hardware MAC:</span>
                    <span class="info-val">{client_mac or 'Detecting...'}</span>
                </div>
                <div class="info-row">
                    <span>Assigned Client IP:</span>
                    <span class="info-val">{client_ip or 'Auto (DHCP)'}</span>
                </div>
                <div class="info-row">
                    <span>Gateway Gateway Node:</span>
                    <span class="info-val">{gw_addr}</span>
                </div>
            </div>

            <div class="quota-banner">
                <strong>Standard Quota:</strong> 1 GiB/Day (1,024 MiB binary standard).
                Netfilter enforces strict 85% download (~870 MiB) / 15% upload (~154 MiB) split.
                Resets daily at 00:00 (Midnight).
            </div>

            <div id="progressCard">
                <div class="spinner"></div>
                <h3 id="progressTitle" style="font-size: 16px; font-weight: 700; margin-bottom: 6px;">Authenticating...</h3>
                <p id="progressDesc" style="font-size: 13px; color: var(--text-muted);">Verifying student credentials and applying gateway quotas.</p>
                <div id="redirectActions" style="margin-top: 16px; display: none;">
                    <a id="manualRedirectBtn" href="#" class="btn btn-primary" style="text-decoration: none;">Continue to Destination</a>
                </div>
            </div>

            <form id="loginForm" action="/api/v1/gateway/portal/submit" method="POST">
                <input type="hidden" name="client_mac" id="clientMacInput" value="{client_mac}">
                <input type="hidden" name="client_ip" id="clientIpInput" value="{client_ip}">
                <input type="hidden" name="hid" id="hidInput" value="{hid}">
                <input type="hidden" name="gatewayaddress" id="gwAddrInput" value="{gw_addr}">
                <input type="hidden" name="authdir" id="authdirInput" value="{authdir}">
                <input type="hidden" name="redir_url" id="redirInput" value="{redir_url}">
                <input type="hidden" name="fas_blob" id="fasBlobInput" value="{fas_raw}">

                <div class="form-group">
                    <label class="form-label" for="usnInput">College USN / Student ID</label>
                    <input class="form-input" type="text" id="usnInput" name="college_usn" placeholder="e.g. DEMO-USN-CSE01" required autofocus autocomplete="username">
                    <div class="demo-pills">
                        <span style="font-size: 11px; color: var(--text-muted); align-self: center;">Quick fill:</span>
                        <button type="button" class="demo-pill" onclick="fillDemo('DEMO-USN-CSE01', 'Campus@2026')">CSE Student 1</button>
                        <button type="button" class="demo-pill" onclick="fillDemo('DEMO-USN-IT02', 'Campus@2026')">IT Student 2</button>
                        <button type="button" class="demo-pill" onclick="fillDemo('DEMO-USN-EXH05', 'Campus@2026')">Quota Exhausted Demo</button>
                    </div>
                </div>

                <div class="form-group">
                    <label class="form-label" for="passInput">Account Password</label>
                    <input class="form-input" type="password" id="passInput" name="password" placeholder="••••••••" required autocomplete="current-password">
                </div>

                <div class="form-group">
                    <label class="form-label" for="otpInput">Demo Verification Code (Optional)</label>
                    <div class="otp-row">
                        <input class="form-input" type="text" id="otpInput" name="otp_code" placeholder="6-digit OTP (or leave empty)" maxlength="6">
                        <button type="button" class="otp-btn" id="genOtpBtn" onclick="requestOtp()">Generate OTP</button>
                    </div>
                </div>

                <button type="submit" class="btn btn-primary" id="submitBtn">
                    Connect to Campus Internet
                </button>
            </form>
        </div>

        <div class="footer">
            Final-Year Major Project • AI Wi-Fi Optimization & Dead-Zone Prediction System<br>
            Protected by OpenNDS FAS Level 1 & OpenWrt 25.12.5 Firewall
        </div>
    </div>

    <script>
        function fillDemo(usn, pass) {{
            document.getElementById('usnInput').value = usn;
            document.getElementById('passInput').value = pass;
        }}

        async function requestOtp() {{
            var usn = document.getElementById('usnInput').value.trim();
            if (!usn) {{
                alert('Please enter your College USN first.');
                return;
            }}
            var btn = document.getElementById('genOtpBtn');
            btn.disabled = true;
            btn.innerText = 'Generating...';
            try {{
                var res = await fetch('/api/v1/gateway/otp/request', {{
                    method: 'POST',
                    headers: {{ 'Content-Type': 'application/json' }},
                    body: JSON.stringify({{ college_usn: usn }})
                }});
                var data = await res.json();
                if (data.demo_otp) {{
                    document.getElementById('otpInput').value = data.demo_otp;
                    alert('Demo OTP Generated: ' + data.demo_otp + ' (In-memory simulation, zero paid SMS)');
                }} else {{
                    alert('Failed to generate OTP: ' + (data.detail || 'Unknown error'));
                }}
            }} catch (err) {{
                alert('OTP generation error: ' + err.message);
            }} finally {{
                btn.disabled = false;
                btn.innerText = 'Generate OTP';
            }}
        }}

        // Client-side async submission enhancement
        document.getElementById('loginForm').addEventListener('submit', async function(e) {{
            e.preventDefault();

            var form = document.getElementById('loginForm');
            var progress = document.getElementById('progressCard');
            var submitBtn = document.getElementById('submitBtn');
            var progressTitle = document.getElementById('progressTitle');
            var progressDesc = document.getElementById('progressDesc');
            var redirectActions = document.getElementById('redirectActions');
            var manualBtn = document.getElementById('manualRedirectBtn');

            var usn = document.getElementById('usnInput').value.trim();
            var password = document.getElementById('passInput').value;
            var clientMac = document.getElementById('clientMacInput').value.trim() || '00:50:56:c0:00:02';
            var clientIp = document.getElementById('clientIpInput').value.trim() || '192.168.214.100';
            var hid = document.getElementById('hidInput').value.trim();
            var gwAddr = document.getElementById('gwAddrInput').value.trim() || '192.168.214.2:2050';
            var authdir = document.getElementById('authdirInput').value.trim() || 'opennds_auth';
            var redirUrl = document.getElementById('redirInput').value.trim() || 'https://www.google.com';
            var otpCode = document.getElementById('otpInput').value.trim();

            form.style.display = 'none';
            progress.style.display = 'block';
            progressTitle.innerText = 'Authorizing on Gateway...';
            progressDesc.innerText = 'Verifying ' + usn + ' and setting OpenWrt netfilter quotas...';

            try {{
                var payload = {{
                    college_usn: usn,
                    student_id: usn,
                    password: password,
                    client_mac: clientMac,
                    client_ip: clientIp,
                    hid: hid || null,
                    gatewayaddress: gwAddr,
                    authdir: authdir,
                    redir_url: redirUrl,
                    otp_code: otpCode || null
                }};

                var res = await fetch('/api/v1/gateway/login', {{
                    method: 'POST',
                    headers: {{ 'Content-Type': 'application/json' }},
                    body: JSON.stringify(payload)
                }});

                var data = await res.json();

                if (!res.ok) {{
                    form.style.display = 'block';
                    progress.style.display = 'none';
                    alert('Login Failed: ' + (data.detail || data.message || 'Authentication rejected.'));
                    return;
                }}

                progressTitle.innerText = 'Access Granted!';
                progressTitle.style.color = '#15803d';
                progressDesc.innerHTML = 'Welcome, <strong>' + (data.name || usn) + '</strong>!<br>' +
                    'Remaining Data Today: <strong>' + data.remaining_quota_mb + ' MiB</strong><br>' +
                    'Download Cap: ' + data.download_quota_mb + ' MiB | Upload Cap: ' + data.upload_quota_mb + ' MiB<br>' +
                    'Session Timeout: ' + data.session_timeout_mins + ' mins.<br><br>' +
                    '<em>Completing OpenNDS handshake and opening firewall...</em>';

                var targetUrl = data.authaction_url || data.redir_url || redirUrl;
                manualBtn.href = targetUrl;
                redirectActions.style.display = 'block';

                setTimeout(function() {{
                    window.location.href = targetUrl;
                }}, 1500);

            }} catch (err) {{
                form.style.display = 'block';
                progress.style.display = 'none';
                alert('Gateway Connection Error: ' + err.message);
            }}
        }});
    </script>
</body>
</html>
"""
