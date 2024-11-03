document.addEventListener("DOMContentLoaded", function() {
    const lazyImages = document.querySelectorAll('.lazy-load');

    if ("IntersectionObserver" in window) {
        let lazyImageObserver = new IntersectionObserver(function(entries, observer) {
            entries.forEach(function(entry) {
                if (entry.isIntersecting) {
                    let lazyImage = entry.target;
                    lazyImage.src = lazyImage.dataset.src;
                    lazyImage.classList.remove('lazy-load');
                    lazyImage.addEventListener('load', function() {
                        // 当图片加载完成后，移除牛顿摆动画
                        const cradle = lazyImage.nextElementSibling;
                        cradle.style.opacity = 0;
                        setTimeout(() => cradle.remove(), 500); // 渐变消失后移除
                        lazyImageObserver.unobserve(lazyImage);
                    });
                }
            });
        });

        lazyImages.forEach(function(lazyImage) {
            lazyImageObserver.observe(lazyImage);
        });
    } else {
        // 如果不支持 Intersection Observer，则直接加载所有图片
        lazyImages.forEach(function(lazyImage) {
            lazyImage.src = lazyImage.dataset.src;
            lazyImage.classList.remove('lazy-load');
            const cradle = lazyImage.nextElementSibling;
            cradle.style.opacity = 0;
            setTimeout(() => cradle.remove(), 500); // 渐变消失后移除
        });
    }

    // 处理分页点击事件
    const paginationLinks = document.querySelectorAll('.pagination a');
    paginationLinks.forEach(link => {
        link.addEventListener('click', function(event) {
            event.preventDefault();

            // 移除所有分页链接上的.current类
            paginationLinks.forEach(l => l.classList.remove('current'));

            // 在被点击的链接上添加.current类
            this.classList.add('current');

            // 重新定向到新的URL
            window.location.href = this.getAttribute('href');
        });
    });
});

// 打开全屏图片
function openFullscreenImage(img) {
    const fullscreenImage = document.getElementById('fullscreen-image');
    const fullscreenImg = document.getElementById('fullscreen-img');
    const downloadLink = document.getElementById('download-link');

    // 使用 data-original 属性获取原图路径
    fullscreenImg.src = img.dataset.original;
    downloadLink.href = img.dataset.original;
    fullscreenImage.style.display = 'flex';
}

// 关闭全屏图片
function closeFullscreenImage() {
    const fullscreenImage = document.getElementById('fullscreen-image');
    fullscreenImage.style.display = 'none';
}