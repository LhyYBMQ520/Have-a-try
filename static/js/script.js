let isInitialRender = true;
document.addEventListener("DOMContentLoaded", function () {
    // render();//不影响但是过度不一样（可注释）
    window.addEventListener("load", function () {
         // 仅在初始加载时执行布局调整
        if (isInitialRender) {

            render();
            isInitialRender = false;
        }
    });
    // 窗口大小改变布局调整
    window.addEventListener("resize", function () {
        if (!isInitialRender) {
            render();
        }
    });

    // 实现瀑布流布局
    function createColumns(ele) {
        let width = ele.offsetWidth;
        let _column;
        if (width >= 1200) {
            _column = 5;
        } else if (width < 1200 && width >= 992) {
            _column = 4;
        } else if (width < 992 && width >= 768) {
            _column = 3;
        } else if (width < 768) {
            _column = 2;
        } else {
            _column = 1;
        }
        return _column;
    }

    function render() {
        let _wrap = document.querySelector(".wrap");
        let _column = createColumns(_wrap);
        let _spacing = 10;
        let _colWidth = (_wrap.offsetWidth - (_column - 1) * _spacing) / _column;
        let _boxList = document.querySelectorAll(".box");
        let _arr = [];

        for (let i = 0; i < _boxList.length; i++) {
            _boxList[i].style.width = _colWidth + "px";
            if (i < _column) {
                _arr.push(_boxList[i].offsetHeight);
                _boxList[i].style.top = 0;
                _boxList[i].style.left = (_colWidth + _spacing) * i + "px";
            } else {
                let min = Math.min(..._arr);
                let index = _arr.indexOf(min);
                _boxList[i].style.top = min + _spacing + "px";
                _boxList[i].style.left = (_spacing + _colWidth) * index + "px";
                _arr[index] += _boxList[i].offsetHeight + _spacing;
            }
        }
    }

    //window.addEventListener("load", render);
    //window.addEventListener("resize", render);

    // 图片懒加载
    const lazyImages = document.querySelectorAll('.lazy-load');
    if ("IntersectionObserver" in window) {
        let lazyImageObserver = new IntersectionObserver(function (entries, observer) {
            entries.forEach(function (entry) {
                if (entry.isIntersecting) {
                    let lazyImage = entry.target;
                    lazyImage.src = lazyImage.dataset.src;
                    lazyImage.onload = function () {
                        // 图片加载完成后调用render函数重新计算布局
                        render();
                    };
                    lazyImage.classList.remove('lazy-load');
                    lazyImageObserver.unobserve(lazyImage);
                }
            });
        });

        lazyImages.forEach(function (lazyImage) {
            lazyImageObserver.observe(lazyImage);
        });
    } else {
        // 如果不支持 Intersection Observer，则直接加载所有图片
        lazyImages.forEach(function (lazyImage) {
            lazyImage.src = lazyImage.dataset.src;
            lazyImage.onload = function () {
                // 图片加载完成后调用render函数重新计算布局
                render();
            };
            lazyImage.classList.remove('lazy-load');
        });
    }


    // 处理分页点击事件
    const paginationLinks = document.querySelectorAll('.pagination a');
    paginationLinks.forEach(link => {
        link.addEventListener('click', function (event) {
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