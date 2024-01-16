function GenshinStyle() {
    // 添加引入<link>格式的字体css
    const linkCss = document.createElement('link');
    linkCss.rel = 'stylesheet';
    linkCss.href = 'https://192960944.r.cdn36.com/chinesefonts3/packages/dymh/dist/DouyinSansBold/result.css';
    document.head.appendChild(linkCss);
    // 更换网页图标
    const icon = document.createElement('link');
    icon.rel = 'icon';
    icon.href = 'https://genshin.mihoyo.com/favicon.ico';
    document.head.appendChild(icon);
    // 调整gradio-app透明度
    document.body.childNodes[1].style.background = "url('https://i.miji.bid/2024/01/14/2186ed3b9dfebe28b6138c400410eb83.png')";
    // 移除<footer>
    document.getElementsByTagName('footer')[0].remove();
}