window.onload = function() {
    // 获取页面上的文字元素
    var textElement = document.getElementsByTagName("h1")[0];

    // 定义每帧动画的回调函数
    function rotateText() {
        // 获取当前文字的角度
        var currentAngle = parseInt(textElement.getAttribute("data-angle")) || 0;
        // 计算下一帧文字的角度
        var nextAngle = (currentAngle + 1) % 360;
        // 设置文字的旋转角度
        textElement.style.transform = "rotate(" + nextAngle + "deg)";
        // 存储下一帧文字的角度
        textElement.setAttribute("data-angle", nextAngle);
        // 在下一帧执行rotateText函数
        requestAnimationFrame(rotateText);
    }

    // 启动动画
    requestAnimationFrame(rotateText);
};