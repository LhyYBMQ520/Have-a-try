let isInitialRender = true;
document.addEventListener("DOMContentLoaded", function () {
    //<!--每groupSize张图片为一组来实现分区地对高度进行懒加载-->
    const groupSize=100
    const imageFileNameGroups=(()=>{
        const result = [];
        // 循环遍历原数组，每groupSize个为一组进行分割
        for (let i = 0; i < imageFileNames.length; i += groupSize) {
            result.push(imageFileNames.slice(i, i + groupSize));  // 使用slice提取每个片段并推入结果数组
        }
        return result;
    })()

    //步进渲染每一组
    let renderGroupPointer=0;
    /**每执行一次这个函数，都会自动步进一次 */
    function renderNextGroup(){
        if(renderGroupPointer>=imageFileNameGroups.length)return;
        const imageFileNameGroup=imageFileNameGroups[renderGroupPointer]
        const galleryContainer = document.getElementById('gallery-container');

        for (let i in imageFileNameGroup) {
            const imageFileName=imageFileNameGroup[i]
            const imageCode = `
            <div class="box">
                <img src="data:image/gif;base64,R0lGODlhAQABAIAAAP///wAAACH5BAEAAAAALAAAAAABAAEAAAICRAEAOw==" 
                    alt="${imageFileName}" 
                    class="lazy-load" 
                    data-src="/image/${imageFileName}" 
                    data-original="/original/${imageFileName}" 
                    data-groupid="${renderGroupPointer}" 
                    data-grouporder="${i}" 
                    onclick="openFullscreenImage(this)"
                >
            </div>
            `;
            
            // 使用 innerHTML 追加内容到 <span> 容器
            //imageGroupContainer.innerHTML += imageCode;

            galleryContainer.innerHTML += imageCode
        }
        //新的元素加入后，要为新元素重新渲染，渲染完了才能懒加载
        render()
        //新的元素加入后，需要重新设置一遍懒加载的监听
        refresh_lazy_load()
        renderGroupPointer++;
    }

    for(let imageFileNameGroup of imageFileNameGroups){

    }



    

    // render();//不影响但是过度不一样（可注释）
    window.addEventListener("load", function () {
         // 仅在初始加载时执行布局调整
        if (isInitialRender) {
            //开始时先渲染一组让屏幕上有图片，并且用这组来触发下一组的渲染
            renderNextGroup()

            render();
            isInitialRender = false;
            //初始加载时，开始懒加载逻辑
            refresh_lazy_load()
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

    function refresh_lazy_load(){
        // 图片懒加载
        const lazyImages = document.querySelectorAll('.lazy-load');
        if ("IntersectionObserver" in window) {
            let lazyImageObserver = new IntersectionObserver(function (entries, observer) {
                entries.forEach(function (entry) {if (entry.isIntersecting) {
                    //进入视口的是图片，渲染图片
                    let lazyImage = entry.target;
                    lazyImage.src = lazyImage.dataset.src;
                    lazyImage.onload = function () {
                        // 图片加载完成后调用render函数重新计算布局
                        render();
                    };
                    lazyImage.classList.remove('lazy-load');
                    lazyImageObserver.unobserve(lazyImage);
                    if(lazyImage.dataset.grouporder==groupSize-1){
                        //最后一张图片露出来的时候加载下一组
                        renderNextGroup()
                    }
                }});
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
    const fullscreenImg = document.getElementById('fullscreen-img');
    fullscreenImg.src = "";
}