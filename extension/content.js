(function() {
    if (window.hasSnapBiliInjected) return;
    window.hasSnapBiliInjected = true;

    const SERVER_URL = 'http://127.0.0.1:5000';

    // Inject Floating SnapBili Widget Button
    function injectWidget() {
        if (document.getElementById('snapbili-widget-btn')) return;

        const btn = document.createElement('div');
        btn.id = 'snapbili-widget-btn';
        btn.innerHTML = `
            <div class="snapbili-btn-content">
                <span class="snapbili-icon">⚡</span>
                <span class="snapbili-label">Tải Video downloader</span>
            </div>
        `;
        document.body.appendChild(btn);

        btn.addEventListener('click', () => {
            toggleModal();
        });
    }

    // Modal Panel
    function toggleModal() {
        let modal = document.getElementById('snapbili-modal');
        if (modal) {
            modal.style.display = modal.style.display === 'none' ? 'block' : 'none';
            return;
        }

        modal = document.createElement('div');
        modal.id = 'snapbili-modal';
        modal.innerHTML = `
            <div class="snapbili-modal-content">
                <div class="snapbili-modal-header">
                    <h3>⚡ downloader</h3>
                    <span class="snapbili-close" id="snapbiliClose">&times;</span>
                </div>
                <div class="snapbili-modal-body">
                    <p class="snapbili-sub">Tải video này không logo, chất lượng cao nhất & phụ đề:</p>
                    <div class="snapbili-actions">
                        <button class="snap-btn snap-btn-hd" id="snapHd">📥 Tải HD / 4K (Không Logo)</button>
                        <button class="snap-btn snap-btn-sd" id="snapSd">🎬 Tải SD</button>
                        <button class="snap-btn snap-btn-mp3" id="snapMp3">🎵 Tải Nhạc MP3</button>
                    </div>
                    <div class="snapbili-status" id="snapStatus" style="display:none;"></div>
                </div>
            </div>
        `;
        document.body.appendChild(modal);

        document.getElementById('snapbiliClose').addEventListener('click', () => {
            modal.style.display = 'none';
        });

        document.getElementById('snapHd').addEventListener('click', () => triggerDownload('hd'));
        document.getElementById('snapSd').addEventListener('click', () => triggerDownload('sd'));
        document.getElementById('snapMp3').addEventListener('click', () => triggerDownload('mp3'));
    }

    async function triggerDownload(type) {
        const statusEl = document.getElementById('snapStatus');
        statusEl.style.display = 'block';
        statusEl.textContent = `🚀 Đã chuyển tác vụ tải ngầm... Bạn có thể chuyển tab hoặc lướt web thoải mái!`;

        const currentUrl = window.location.href;

        chrome.runtime.sendMessage({
            action: 'START_DOWNLOAD',
            url: currentUrl,
            type: type
        }, (response) => {
            if (response && response.error) {
                statusEl.textContent = `❌ Lỗi: ${response.error}`;
            } else {
                statusEl.textContent = `✅ Tải ngầm hoàn tất! Đã lưu 3 file.`;
                setTimeout(() => { statusEl.style.display = 'none'; }, 4000);
            }
        });
    }

    // Wait for DOM
    if (document.readyState === 'loading') {
        document.addEventListener('DOMContentLoaded', injectWidget);
    } else {
        injectWidget();
    }
})();
