// 更换网页图标
function modifyIcon() {
    const icon = document.createElement('link');
    icon.rel = 'icon';
    icon.href = 'https://genshin.mihoyo.com/favicon.ico';
    document.head.appendChild(icon);
}