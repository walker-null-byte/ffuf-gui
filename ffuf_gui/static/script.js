document.addEventListener('DOMContentLoaded', () => {
    const runBtn = document.getElementById('btn-run');
    const stopBtn = document.getElementById('btn-stop');
    const form = document.getElementById('config-form');
    const previewEl = document.getElementById('command-preview');
    const statusEl = document.getElementById('status-indicator');
    const resultsBody = document.getElementById('results-body');
    const logOutput = document.getElementById('log-output');
    const statsArea = document.getElementById('stats-area');

    /* No tabs needed for new layout */

    // --- Wordlists ---
    let wlCount = 1;
    const addWlBtn = document.getElementById('add-wordlist');
    
    if (addWlBtn) {
        addWlBtn.addEventListener('click', () => {
            const container = document.getElementById('wordlist-container');
            const div = document.createElement('div');
            div.className = 'wordlist-item';
            div.innerHTML = `
                <input type="text" name="wl_path_${wlCount}" placeholder="Click Browse or paste full path" class="wl-path" style="flex: 1;">
                <button type="button" class="btn-browse" data-target="wl_path_${wlCount}">📂</button>
                <input type="text" name="wl_key_${wlCount}" value="FUZZ" placeholder="Key" class="wl-key">
                <button type="button" class="btn-remove">x</button>
            `;
            container.appendChild(div);
            wlCount++;
            updatePreview();
        });
    }

    const wlContainer = document.getElementById('wordlist-container');
    if (wlContainer) {
        wlContainer.addEventListener('click', async (e) => {
            // Handle remove button
            if (e.target.classList.contains('btn-remove')) {
                e.target.parentElement.remove();
                updatePreview();
            }
            // Handle browse button
            if (e.target.classList.contains('btn-browse')) {
                const targetInputName = e.target.dataset.target;
                const targetInput = document.querySelector(`input[name="${targetInputName}"]`);
                
                if (targetInput) {
                    e.target.disabled = true;
                    e.target.textContent = '...';
                    
                    try {
                        const resp = await fetch('/api/browse', { method: 'POST' });
                        const data = await resp.json();
                        
                        if (data.success && data.path) {
                            targetInput.value = data.path;
                            updatePreview();
                        }
                    } catch (err) {
                        console.error('Browse error:', err);
                    }
                    
                    e.target.disabled = false;
                    e.target.textContent = '📂';
                }
            }
        });
    }

    // --- Browse for Output File ---
    const browseOutputBtn = document.getElementById('browse-output');
    if (browseOutputBtn) {
        browseOutputBtn.addEventListener('click', async () => {
            const targetInput = document.querySelector('input[name="output_file"]');
            
            browseOutputBtn.disabled = true;
            browseOutputBtn.textContent = '...';
            
            try {
                const resp = await fetch('/api/browse_save', { method: 'POST' });
                const data = await resp.json();
                
                if (data.success && data.path) {
                    targetInput.value = data.path;
                    updatePreview();
                }
            } catch (err) {
                console.error('Browse error:', err);
            }
            
            browseOutputBtn.disabled = false;
            browseOutputBtn.textContent = '📂';
        });
    }

    // --- Preview ---
    function updatePreview() {
        const formData = new FormData(form);
        let cmd = "ffuf";
        
        // URL
        const url = formData.get('url');
        if (url) cmd += ` -u "${url}"`;

        // Wordlists
        // We need to iterate over wl_path_X
        for (const [key, val] of formData.entries()) {
            if (key.startsWith('wl_path_') && val) {
                const id = key.split('_')[2];
                const keyWord = formData.get(`wl_key_${id}`) || 'FUZZ';
                // Only add :KEYWORD if it's not the default FUZZ
                if (keyWord && keyWord !== 'FUZZ') {
                    cmd += ` -w ${val}:${keyWord}`;
                } else {
                    cmd += ` -w ${val}`;
                }
            }
        }

        // Method
        const method = formData.get('method');
        if (method && method !== 'GET') cmd += ` -X ${method}`;

        // Data
        const data = formData.get('data');
        if (data) cmd += ` -d "${data.replace(/"/g, '\\"')}"`;

        // Headers
        const headers = formData.get('headers');
        if (headers) {
            headers.split('\n').filter(h => h.trim()).forEach(h => {
                cmd += ` -H "${h.trim().replace(/"/g, '\\"')}"`;
            });
        }

        // Matchers
        ['mc', 'ms', 'mw', 'ml', 'mr'].forEach(k => {
            const v = formData.get(k);
            if(v) cmd += ` -${k} ${v}`;
        });

        // Filters
        ['fc', 'fs', 'fw', 'fl', 'fr'].forEach(k => {
            const v = formData.get(k);
            if(v) cmd += ` -${k} ${v}`;
        });

        // General
        if (formData.get('threads')) cmd += ` -t ${formData.get('threads')}`;
        if (formData.get('timeout')) cmd += ` -timeout ${formData.get('timeout')}`;
        if (formData.get('recursion')) {
            cmd += ` -recursion`;
            if (formData.get('recursion_depth') && formData.get('recursion_depth') !== '0') {
                cmd += ` -recursion-depth ${formData.get('recursion_depth')}`;
            }
        }
        if (formData.get('ignore_body')) cmd += ` -ignore-body`;
        if (formData.get('follow_redirects')) cmd += ` -r`;
        
        // Output options
        if (formData.get('output_file')) cmd += ` -o "${formData.get('output_file')}"`;
        if (formData.get('output_format')) cmd += ` -of ${formData.get('output_format')}`;
        if (formData.get('silent')) cmd += ` -s`;
        if (formData.get('verbose')) cmd += ` -v`;
        if (formData.get('colors')) cmd += ` -c`;

        previewEl.textContent = cmd;
    }

    // Update preview on any form changes (input for text, change for select/checkbox)
    form.addEventListener('input', updatePreview);
    form.addEventListener('change', updatePreview);
    
    // Initial preview after a short delay to ensure form is fully loaded
    setTimeout(updatePreview, 100);

    // --- Execution ---
    runBtn.addEventListener('click', async () => {
        const formData = new FormData(form);
        const config = {
            url: formData.get('url'),
            method: formData.get('method'),
            data: formData.get('data'),
            headers: formData.get('headers') ? formData.get('headers').split('\n').filter(x=>x.trim()) : [],
            wordlists: [],
            // Matchers
            mc: formData.get('mc'), ms: formData.get('ms'), mw: formData.get('mw'), ml: formData.get('ml'), mr: formData.get('mr'),
            // Filters
            fc: formData.get('fc'), fs: formData.get('fs'), fw: formData.get('fw'), fl: formData.get('fl'), fr: formData.get('fr'),
            // General
            threads: parseInt(formData.get('threads') || 40),
            timeout: parseInt(formData.get('timeout') || 10),
            recursion: formData.get('recursion') === 'on',
            recursion_depth: parseInt(formData.get('recursion_depth') || 0),
            ignore_body: formData.get('ignore_body') === 'on',
            follow_redirects: formData.get('follow_redirects') === 'on',
            // Output options
            output_file: formData.get('output_file') || '',
            output_format: formData.get('output_format') || '',
            silent: formData.get('silent') === 'on',
            verbose: formData.get('verbose') === 'on',
            colors: formData.get('colors') === 'on'
        };

        // Collect wordlists
        for (const [key, val] of formData.entries()) {
            if (key.startsWith('wl_path_') && val) {
                const id = key.split('_')[2];
                config.wordlists.push({
                    path: val,
                    keyword: formData.get(`wl_key_${id}`) || 'FUZZ'
                });
            }
        }

        try {
            statusEl.innerText = "Starting...";
            statusEl.className = "status running";
            resultsBody.innerHTML = ""; // Clear table
            logOutput.innerText = "";
            
            const resp = await fetch('/api/run', {
                method: 'POST',
                headers: {'Content-Type': 'application/json'},
                body: JSON.stringify(config)
            });
            const data = await resp.json();
            
            if (resp.ok) {
                statusEl.innerText = "Running";
                connectSSE();
                runBtn.disabled = true;
                stopBtn.disabled = false;
            } else {
                statusEl.innerText = "Error";
                statusEl.className = "status error";
                alert("Error: " + data.message);
            }
        } catch (e) {
            console.error(e);
            statusEl.innerText = "Error";
            statusEl.className = "status error";
        }
    });

    stopBtn.addEventListener('click', async () => {
        try {
            await fetch('/api/stop', { method: 'POST' });
            statusEl.innerText = "Stopping...";
        } catch (e) {
            console.error(e);
        }
    });

    // --- Streaming ---
    let eventSource = null;
    let resultCount = 0;
    
    function connectSSE() {
        if (eventSource) eventSource.close();
        resultCount = 0;
        
        // Add initial message to log
        logOutput.textContent = "[" + new Date().toLocaleTimeString() + "] Connecting to ffuf stream...\n";
        
        eventSource = new EventSource('/api/stream');
        
        eventSource.onmessage = (e) => {
            try {
                const msg = JSON.parse(e.data);
                
                if (msg.type === 'result') {
                    addResultRow(msg.data);
                    resultCount++;
                    statsArea.textContent = `Results: ${resultCount}`;
                } else if (msg.type === 'log') {
                    // Format log with timestamp
                    const timestamp = new Date().toLocaleTimeString();
                    logOutput.textContent += `[${timestamp}] ${msg.data}\n`;
                    // Auto-scroll to bottom
                    logOutput.scrollTop = logOutput.scrollHeight;
                } else if (msg.type === 'status') {
                    if (msg.data === 'finished' || msg.data === 'stopped') {
                        const timestamp = new Date().toLocaleTimeString();
                        logOutput.textContent += `[${timestamp}] === ${msg.data.toUpperCase()} ===\n`;
                        logOutput.scrollTop = logOutput.scrollHeight;
                        
                        statusEl.textContent = msg.data === 'stopped' ? "Stopped" : "Finished";
                        statusEl.className = "status idle";
                        stopBtn.disabled = true;
                        runBtn.disabled = false;
                        eventSource.close();
                    }
                } else if (msg.type === 'error') {
                    const timestamp = new Date().toLocaleTimeString();
                    logOutput.textContent += `[${timestamp}] [ERROR] ${msg.data}\n`;
                    logOutput.scrollTop = logOutput.scrollHeight;
                }
            } catch (parseError) {
                console.error("Parse error:", parseError, e.data);
            }
        };
        
        eventSource.onerror = (e) => {
            console.error("SSE Error", e);
            eventSource.close();
            // Check if we were still running
            if (statusEl.textContent === "Running") {
                const timestamp = new Date().toLocaleTimeString();
                logOutput.textContent += `[${timestamp}] [ERROR] Connection lost\n`;
                statusEl.textContent = "Connection Lost";
                statusEl.className = "status error";
                stopBtn.disabled = true;
                runBtn.disabled = false;
            }
        };
    }

    function addResultRow(item) {
        // item structure from ffuf -json:
        // { "input": {"FUZZ": "val"}, "position": 1, "status": 200, "length": 123, "words": 20, "lines": 5, "content_type": "", "redirectlocation": "", "url": ""}
        
        const row = document.createElement('tr');
        // Status/Time
        // FFUF json has 'time' string or we can use status
        row.innerHTML = `
            <td><span class="badge status-${item.status}">${item.status}</span></td>
            <td>${item.length}</td>
            <td>${item.words}</td>
            <td>${item.lines}</td>
            <td title="${item.url}">${Object.values(item.input).join(', ')}</td>
            <td>${item.content_type}</td>
        `;
        // Check for redirect
        if (item.redirectlocation) {
             row.innerHTML += `<div class="small-redirect">-> ${item.redirectlocation}</div>`;
        }
        
        resultsBody.prepend(row);
        
        // Limit rows to prevent DOM explosion
        if (resultsBody.children.length > 1000) {
            resultsBody.lastElementChild.remove();
        }
    }

    document.getElementById('clear-log').addEventListener('click', () => {
        resultsBody.innerHTML = "";
        logOutput.innerText = "";
    });
});

