// 徕欧联系表单提交处理
// 适用于所有页面（首页、联系页、国家页面）

(function() {
    'use strict';

    // Google Apps Script Web App URL
    const SCRIPT_URL = 'https://script.google.com/macros/s/AKfycbxVJAtrf4ZMSC-en6xodCJ6evYcw6699t_Hoh0FZkVb38vZclQVVtbvA8J0jZi1NXU/exec';

    // 初始化表单处理
    function initFormHandler() {
        const form = document.getElementById('contactForm');
        if (!form) return;

        form.addEventListener('submit', async function(e) {
            e.preventDefault();

            const submitBtn = document.getElementById('submitBtn');
            const formMessage = document.getElementById('formMessage');
            const formData = new FormData(this);

            // 获取国家信息（国家页面有 data-country 属性）
            const country = this.getAttribute('data-country') || '';

            // 构建数据对象
            const data = {
                name: formData.get('name'),
                phone: formData.get('phone'),
                wechat: formData.get('wechat') || '',
                email: formData.get('email'),
                service: formData.get('service') || '',
                message: formData.get('message'),
                country: country
            };

            // 禁用提交按钮
            if (submitBtn) {
                submitBtn.disabled = true;
                submitBtn.textContent = '发送中...';
            }
            if (formMessage) {
                formMessage.textContent = '';
                formMessage.style.color = '';
            }

            try {
                const response = await fetch(SCRIPT_URL, {
                    method: 'POST',
                    body: JSON.stringify(data),
                    headers: {
                        'Content-Type': 'application/json'
                    }
                });

                const result = await response.json();

                if (formMessage) {
                    if (result.success) {
                        formMessage.style.color = '#28a745';
                        formMessage.textContent = result.message;
                        form.reset();
                    } else {
                        formMessage.style.color = '#dc3545';
                        formMessage.textContent = result.message || '发送失败，请稍后重试';
                    }
                }
            } catch (error) {
                if (formMessage) {
                    formMessage.style.color = '#dc3545';
                    formMessage.textContent = '网络错误，请检查网络连接后重试';
                }
            } finally {
                if (submitBtn) {
                    submitBtn.disabled = false;
                    submitBtn.textContent = '立即咨询';
                }
            }
        });
    }

    // DOM 加载完成后初始化
    if (document.readyState === 'loading') {
        document.addEventListener('DOMContentLoaded', initFormHandler);
    } else {
        initFormHandler();
    }
})();
