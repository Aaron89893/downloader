const SERVER_URL = 'http://127.0.0.1:5000';

async function getNetscapeCookies(urlStr) {
    try {
        const parsedUrl = new URL(urlStr);
        const host = parsedUrl.hostname;
        const parts = host.split('.');
        let domainQuery = host;
        if (parts.length >= 2) {
            domainQuery = parts.slice(-2).join('.');
        }

        let cookies = await chrome.cookies.getAll({ domain: domainQuery });
        if (!cookies || cookies.length === 0) {
            cookies = await chrome.cookies.getAll({ url: urlStr });
        }
        if (!cookies || cookies.length === 0) return null;
        
        let lines = ["# Netscape HTTP Cookie File"];
        cookies.forEach(c => {
            const domainMatch = c.domain.startsWith('.') ? 'TRUE' : 'FALSE';
            const path = c.path || '/';
            const secure = c.secure ? 'TRUE' : 'FALSE';
            const expiration = c.expirationDate ? Math.floor(c.expirationDate) : Math.floor(Date.now() / 1000 + 86400);
            lines.push(`${c.domain}\t${domainMatch}\t${path}\t${secure}\t${expiration}\t${c.name}\t${c.value}`);
        });
        return lines.join('\n');
    } catch (e) {
        return null;
    }
}

document.addEventListener('DOMContentLoaded', async () => {
    const statusDot = document.getElementById('statusDot');
    const statusText = document.getElementById('statusText');

    const urlInput = document.getElementById('urlInput');
    const downloadFastBtn = document.getElementById('downloadFastBtn');
    const analyzeBtn = document.getElementById('analyzeBtn');

    const videoCard = document.getElementById('videoCard');
    const videoThumb = document.getElementById('videoThumb');
    const videoDuration = document.getElementById('videoDuration');
    const videoTitle = document.getElementById('videoTitle');
    const videoAuthor = document.getElementById('videoAuthor');
    const qualitySelect = document.getElementById('qualitySelect');
    const dlCustomBtn = document.getElementById('dlCustomBtn');

    const progressBox = document.getElementById('progressBox');
    const progressText = document.getElementById('progressText');
    const errorBox = document.getElementById('errorBox');

    let currentSessData = '';

    // Check server connection
    try {
        const checkRes = await fetch(SERVER_URL + '/');
        if (checkRes.ok) {
            statusDot.className = 'status-dot green';
            statusText.textContent = 'Server Ready';
        } else {
            statusDot.className = 'status-dot red';
            statusText.textContent = 'Server Offline';
        }
    } catch (e) {
        statusDot.className = 'status-dot red';
        statusText.textContent = 'Server Offline';
    }

    // Auto extract Bilibili SESSDATA cookie from current tab if available
    try {
        const cookie = await chrome.cookies.get({ url: 'https://www.bilibili.com', name: 'SESSDATA' });
        if (cookie && cookie.value) {
            currentSessData = cookie.value;
        }
    } catch (e) {}

    // AUTO GET CURRENT ACTIVE TAB URL ON OPEN
    chrome.tabs.query({ active: true, currentWindow: true }, (tabs) => {
        if (tabs && tabs[0] && tabs[0].url) {
            const activeUrl = tabs[0].url;
            if (activeUrl.startsWith('http://') || activeUrl.startsWith('https://')) {
                urlInput.value = activeUrl;
            }
        }
    });

    // Fast 1-Click Download Button (1080p Default)
    downloadFastBtn.addEventListener('click', () => {
        const url = urlInput.value.trim();
        if (!url) {
            showError('Vui lòng nhập đường dẫn URL.');
            return;
        }
        triggerDownload(url, '1080p');
    });

    // Analyze Button (Fetches formats & details via Background Service Worker)
    analyzeBtn.addEventListener('click', () => {
        const url = urlInput.value.trim();
        if (!url) {
            showError('Vui lòng nhập đường dẫn URL.');
            return;
        }

        showError('');
        setProgress(true, 'Đang phân tích định dạng...');

        chrome.runtime.sendMessage({
            action: 'ANALYZE_VIDEO',
            url: url,
            sessdata: currentSessData
        }, (data) => {
            if (chrome.runtime.lastError) {
                showError('Lỗi phân tích: ' + chrome.runtime.lastError.message);
                setProgress(false);
                return;
            }

            if (!data || data.error) {
                showError(data ? data.error : 'Phân tích thất bại.');
                setProgress(false);
                return;
            }

            videoThumb.src = data.thumbnail.startsWith('/') ? SERVER_URL + data.thumbnail : data.thumbnail;
            videoTitle.textContent = data.title;
            videoAuthor.textContent = 'Tác giả: ' + data.uploader;
            videoDuration.textContent = data.duration;

            qualitySelect.innerHTML = '';
            data.qualities.forEach(q => {
                const opt = document.createElement('option');
                opt.value = q.id;
                opt.textContent = q.name;
                qualitySelect.appendChild(opt);
            });

            videoCard.style.display = 'block';
            setProgress(false);
        });
    });

    // Custom Download Button inside Video Card
    dlCustomBtn.addEventListener('click', () => {
        const url = urlInput.value.trim();
        const quality = qualitySelect.value;
        if (url) {
            triggerDownload(url, quality);
        }
    });

    function triggerDownload(url, quality = '1080p') {
        showError('');
        setProgress(true, `Đã khởi chạy tác vụ tải (${quality})...`);

        chrome.runtime.sendMessage({
            action: 'START_DOWNLOAD',
            url: url,
            type: quality,
            sessdata: currentSessData
        }, (response) => {
            if (chrome.runtime.lastError) {
                showError('Lỗi kết nối background script: ' + chrome.runtime.lastError.message);
                setProgress(false);
                return;
            }

            if (response && response.error) {
                showError(response.error);
                setProgress(false);
            } else {
                setProgress(true, `✅ Tải ngầm hoàn tất! Đã lưu 2 file.`);
                setTimeout(() => setProgress(false), 5000);
            }
        });
    }

    function setProgress(show, text = '') {
        progressBox.style.display = show ? 'block' : 'none';
        if (text) progressText.textContent = text;
    }

    function showError(msg) {
        if (msg) {
            errorBox.style.display = 'block';
            errorBox.textContent = msg;
        } else {
            errorBox.style.display = 'none';
            errorBox.textContent = '';
        }
    }
});
