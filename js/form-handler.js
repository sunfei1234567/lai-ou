// 徕欧联系表单提交处理
// 适用于所有页面（首页、联系页、国家页面）

(function() {
    'use strict';

    // 后端 API 地址
    const API_URL = 'http://127.0.0.1:10000/api/consultations';

    // 初始化表单处理
    function initFormHandler() {
        // 获取所有联系表单（支持多个表单）
        const forms = document.querySelectorAll('.contact-form');

        forms.forEach(form => {
            form.addEventListener('submit', async function(e) {
                e.preventDefault();

                const submitBtn = this.querySelector('#submitBtn, .submit-btn');
                const formMessage = this.querySelector('#formMessage');

                // 获取表单数据
                const nameInput = this.querySelector('input[name="name"], #name');
                const phoneInput = this.querySelector('input[name="phone"], #phone');
                const emailInput = this.querySelector('input[name="email"], #email');
                const wechatInput = this.querySelector('input[name="wechat"], #wechat');
                const serviceInput = this.querySelector('select[name="service"], #service');
                const messageInput = this.querySelector('textarea[name="message"], #message');

                // 获取国家信息（国家页面有 data-country 属性）
                const country = this.getAttribute('data-country') || '';

                // 构建数据对象
                const data = {
                    name: nameInput ? nameInput.value : '',
                    phone: phoneInput ? phoneInput.value : '',
                    email: emailInput ? emailInput.value : '',
                    company: wechatInput ? wechatInput.value : '', // 微信存入 company 字段
                    service_type: serviceInput ? serviceInput.value : (country ? country + '出海咨询' : ''),
                    message: messageInput ? messageInput.value : ''
                };

                // 验证必填字段
                if (!data.name || !data.phone || !data.message) {
                    if (formMessage) {
                        formMessage.style.color = '#dc3545';
                        formMessage.textContent = '请填写必填项（姓名、电话、留言）';
                    }
                    return;
                }

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
                    const response = await fetch(API_URL, {
                        method: 'POST',
                        headers: {
                            'Content-Type': 'application/json'
                        },
                        body: JSON.stringify(data)
                    });

                    // 检查响应是否成功
                    if (!response.ok) {
                        throw new Error('Network response was not ok');
                    }

                    const result = await response.json();

                    if (formMessage) {
                        if (result.code === 200) {
                            formMessage.style.color = '#28a745';
                            formMessage.textContent = '提交成功！我们会尽快与您联系。';
                            this.reset();
                        } else {
                            formMessage.style.color = '#dc3545';
                            formMessage.textContent = result.message || '提交失败，请稍后重试';
                        }
                    }
                } catch (error) {
                    console.error('提交错误:', error);
                    if (formMessage) {
                        formMessage.style.color = '#dc3545';
                        formMessage.textContent = '网络错误，请稍后重试';
                    }
                } finally {
                    if (submitBtn) {
                        submitBtn.disabled = false;
                        submitBtn.textContent = '立即咨询';
                    }
                }
            });
        });
    }

    // DOM 加载完成后初始化
    if (document.readyState === 'loading') {
        document.addEventListener('DOMContentLoaded', initFormHandler);
    } else {
        initFormHandler();
    }
})();
