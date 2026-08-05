document.addEventListener('DOMContentLoaded', () => {
    const urlInput = document.getElementById('urlInput');
    const pasteBtn = document.getElementById('pasteBtn');
    const downloadBtn = document.getElementById('downloadBtn');
    const btnText = downloadBtn.querySelector('.btn-text');
    const spinner = document.getElementById('spinner');
    const errorMsg = document.getElementById('errorMsg');

    const resultContainer = document.getElementById('resultContainer');
    const resThumb = document.getElementById('resThumb');
    const resTitle = document.getElementById('resTitle');
    const resAuthor = document.getElementById('resAuthor');
    const resDuration = document.getElementById('resDuration');

    const dlHdBtn = document.getElementById('dlHdBtn');
    const dlSdBtn = document.getElementById('dlSdBtn');
    const dlMp3Btn = document.getElementById('dlMp3Btn');
    const dlStatus = document.getElementById('dlStatus');
    const dlStatusText = document.getElementById('dlStatusText');
    const resetBtn = document.getElementById('resetBtn');

    let currentUrl = '';

    // Clipboard Paste
    pasteBtn.addEventListener('click', async () => {
        try {
            const text = await navigator.clipboard.readText();
            if (text) {
                urlInput.value = text.strip ? text.strip() : text.trim();
                showError('');
            }
        } catch (err) {
            console.warn('Clipboard access denied or unavailable', err);
        }
    });

    // Enter key trigger
    urlInput.addEventListener('keypress', (e) => {
        if (e.key === 'Enter') {
            downloadBtn.click();
        }
    });

    // Download Analyze Trigger
    downloadBtn.addEventListener('click', async () => {
        const url = urlInput.value.trim();
        if (!url) {
            showError('Vui lòng dán liên kết video Bilibili.');
            return;
        }

        currentUrl = url;
        setLoading(true);
        showError('');

        try {
            const response = await fetch('/api/analyze', {
                method: 'POST',
                headers: { 'Content-Type': 'application/json' },
                body: JSON.stringify({ url: currentUrl })
            });

            const data = await response.json();

            if (!response.ok || data.error) {
                throw new Error(data.error || 'Phân tích video thất bại.');
            }

            // Render Result
            resThumb.src = data.thumbnail;
            resTitle.textContent = data.title;
            resAuthor.textContent = data.uploader;
            resDuration.textContent = data.duration;

            resultContainer.style.display = 'block';
            resultContainer.scrollIntoView({ behavior: 'smooth' });

        } catch (err) {
            showError(err.message || 'Có lỗi xảy ra khi phân tích liên kết Bilibili.');
            resultContainer.style.display = 'none';
        } finally {
            setLoading(false);
        }
    });

    // Download Quality Handlers
    dlHdBtn.addEventListener('click', () => downloadVideo('hd'));
    dlSdBtn.addEventListener('click', () => downloadVideo('sd'));
    dlMp3Btn.addEventListener('click', () => downloadVideo('mp3'));

    async function downloadVideo(type) {
        if (!currentUrl) return;

        setDlStatus(true, `Đang xử lý tải ${type.toUpperCase()}... Vui lòng chờ trong giây lát (có thể mất 10-30 giây đối với video dài).`);

        try {
            const response = await fetch('/api/download', {
                method: 'POST',
                headers: { 'Content-Type': 'application/json' },
                body: JSON.stringify({ url: currentUrl, type: type })
            });

            const data = await response.json();

            if (!response.ok || data.error) {
                throw new Error(data.error || 'Tải file thất bại.');
            }

            // Trigger file download in browser
            const a = document.createElement('a');
            a.href = data.file_url;
            a.download = data.filename;
            document.body.appendChild(a);
            a.click();
            document.body.removeChild(a);

            setDlStatus(true, `✅ Tải về hoàn tất! Đã lưu file: ${data.filename}`);
            setTimeout(() => setDlStatus(false), 5000);

        } catch (err) {
            alert('Lỗi: ' + (err.message || 'Không thể tải video.'));
            setDlStatus(false);
        }
    }

    // Reset button
    resetBtn.addEventListener('click', () => {
        urlInput.value = '';
        currentUrl = '';
        resultContainer.style.display = 'none';
        showError('');
        window.scrollTo({ top: 0, behavior: 'smooth' });
    });

    function setLoading(isLoading) {
        if (isLoading) {
            downloadBtn.disabled = true;
            btnText.style.display = 'none';
            spinner.style.display = 'block';
        } else {
            downloadBtn.disabled = false;
            btnText.style.display = 'inline';
            spinner.style.display = 'none';
        }
    }

    function setDlStatus(show, text = '') {
        if (show) {
            dlStatus.style.display = 'flex';
            dlStatusText.textContent = text;
        } else {
            dlStatus.style.display = 'none';
        }
    }

    function showError(msg) {
        if (msg) {
            errorMsg.textContent = msg;
            errorMsg.style.display = 'block';
        } else {
            errorMsg.style.display = 'none';
        }
    }
});
