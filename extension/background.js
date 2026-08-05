const SERVER_URL = 'http://127.0.0.1:5000';
let activeTaskCount = 0;

chrome.runtime.onInstalled.addListener(() => {
    chrome.contextMenus.create({
        id: "downloader-context-menu",
        title: "⚡ Tải Video Này (downloader)",
        contexts: ["page", "link"]
    });
});

chrome.contextMenus.onClicked.addListener((info, tab) => {
    if (info.menuItemId === "downloader-context-menu") {
        const targetUrl = info.linkUrl || info.pageUrl || tab.url;
        if (targetUrl) {
            handleBackgroundDownload(targetUrl, '1080p');
        }
    }
});

chrome.runtime.onMessage.addListener((request, sender, sendResponse) => {
    if (request.action === 'START_DOWNLOAD') {
        const { url, type, sessdata } = request;
        handleBackgroundDownload(url, type, sessdata, sendResponse);
        return true; // Keep message channel open for async response
    }
});

async function getNetscapeCookies(urlStr) {
    try {
        const parsedUrl = new URL(urlStr);
        const host = parsedUrl.hostname;
        
        // Extract root domain (e.g. www.douyin.com -> douyin.com, v.douyin.com -> douyin.com)
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

async function handleBackgroundDownload(url, type = '1080p', sessdata = null, sendResponse = null) {
    activeTaskCount++;
    const taskId = 'task_' + Date.now() + '_' + Math.floor(Math.random() * 1000);
    
    // Identify domain for notification
    let domainName = "Video";
    if (url.includes('tiktok.com') || url.includes('douyin.com')) domainName = "TikTok/Douyin";
    else if (url.includes('youtube.com') || url.includes('youtu.be')) domainName = "YouTube";
    else if (url.includes('bilibili.com') || url.includes('b23.tv')) domainName = "Bilibili";

    showNotification(taskId, `🚀 [${domainName}] Đã bắt đầu tải ngầm... (${activeTaskCount} tiến trình đang chạy song song)`);

    const cookiesTxt = await getNetscapeCookies(url);

    fetch(`${SERVER_URL}/api/download`, {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({
            url: url,
            type: type,
            sessdata: sessdata,
            cookies_txt: cookiesTxt
        })
    })
    .then(res => res.json())
    .then(data => {
        activeTaskCount = Math.max(0, activeTaskCount - 1);
        if (data.error) {
            showNotification(taskId + '_err', `❌ Lỗi tải [${domainName}]: ` + data.error);
            if (sendResponse) sendResponse({ success: false, error: data.error });
            return;
        }

        if (data.files && data.files.length > 0) {
            data.files.forEach((f, index) => {
                setTimeout(() => {
                    const fileUrl = SERVER_URL + f.url;
                    // Preserve forward slash for folder structure e.g. "BV1KS4y1i7zL/Title.mp4"
                    let parts = f.filename.split('/');
                    let folder = parts[0].replace(/[\\/*?:"<>|【】！~～]/g, '_');
                    let name = parts.slice(1).join('/').replace(/[\\*?:"<>|【】！~～]/g, '_');
                    let safeFilename = folder + '/' + name;

                    chrome.downloads.download({
                        url: fileUrl,
                        filename: safeFilename,
                        saveAs: false
                    }, (downloadId) => {
                        if (chrome.runtime.lastError) {
                            console.error("Download failed:", chrome.runtime.lastError.message);
                        }
                    });
                }, index * 300);
            });
        } else if (data.file_url) {
            let parts = data.filename.split('/');
            let folder = parts[0].replace(/[\\/*?:"<>|【】！~～]/g, '_');
            let name = parts.slice(1).join('/').replace(/[\\*?:"<>|【】！~～]/g, '_');
            let safeFilename = folder + '/' + name;

            chrome.downloads.download({
                url: SERVER_URL + data.file_url,
                filename: safeFilename,
                saveAs: false
            });
        }

        showNotification(taskId + '_done', `✅ [${domainName}] Tải ngầm hoàn tất! Đã lưu 2 file vào thư mục.`);
        if (sendResponse) sendResponse({ success: true, files: data.files });
    })
    .catch(err => {
        activeTaskCount = Math.max(0, activeTaskCount - 1);
        showNotification(taskId + '_err', `❌ Lỗi kết nối server: ` + err.message);
        if (sendResponse) sendResponse({ success: false, error: err.message });
    });
}

function showNotification(id, message) {
    try {
        if (chrome.notifications) {
            chrome.notifications.create(id, {
                type: 'basic',
                iconUrl: 'icons/icon48.png',
                title: 'downloader',
                message: message
            });
        }
    } catch (e) {
        console.log('Notification error:', e);
    }
}
