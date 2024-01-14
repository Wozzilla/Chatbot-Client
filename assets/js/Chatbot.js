function Chatbot() {
    // 更换网页图标
    const icon = document.createElement('link');
    icon.rel = 'icon';
    icon.href = 'https://genshin.mihoyo.com/favicon.ico';
    document.head.appendChild(icon);
    // 调整gradio-app透明度
    document.body.childNodes[1].style.background = "url('https://i.miji.bid/2024/01/14/2186ed3b9dfebe28b6138c400410eb83.png')";
    // 移除音频部分的清除按钮和标签
    document.getElementById('audioInput').querySelector('label').remove();
    document.getElementsByClassName('svelte-19sk1im')[0].remove();
}