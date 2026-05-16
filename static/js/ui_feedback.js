(function () {
    if (window.__uiFeedbackLoaded) {
        return;
    }
    window.__uiFeedbackLoaded = true;

    var styleId = 'ui-feedback-style';
    var wrapId = 'ui-toast-wrap';
    var dialogRootId = 'ui-dialog-root';

    function ensureStyle() {
        if (document.getElementById(styleId)) {
            return;
        }
        var style = document.createElement('style');
        style.id = styleId;
        style.textContent = [
            '.ui-toast-wrap {',
            '  position: fixed;',
            '  top: 86px;',
            '  right: 24px;',
            '  width: min(88vw, 360px);',
            '  z-index: 99999;',
            '  pointer-events: none;',
            '  display: flex;',
            '  flex-direction: column;',
            '  gap: 12px;',
            '}',
            '.ui-toast-item {',
            '  pointer-events: auto;',
            '  padding: 14px 16px;',
            '  border-radius: 12px;',
            '  border: 1px solid #e7e7e7;',
            '  background: #ffffff;',
            '  color: #222;',
            '  font-size: 15px;',
            '  line-height: 1.55;',
            '  box-shadow: 0 12px 26px rgba(0, 0, 0, 0.16);',
            '  display: flex;',
            '  align-items: center;',
            '  gap: 10px;',
            '  animation: uiToastIn 0.2s ease-out;',
            '}',
            '.ui-toast-icon {',
            '  width: 18px;',
            '  height: 18px;',
            '  border-radius: 50%;',
            '  border: 1px solid #444;',
            '  display: inline-flex;',
            '  align-items: center;',
            '  justify-content: center;',
            '  color: #444;',
            '  font-size: 12px;',
            '  line-height: 1;',
            '  flex-shrink: 0;',
            '}',
            '.ui-toast-text {',
            '  color: #222;',
            '}',
            '@media (max-width: 768px) {',
            '  .ui-toast-wrap {',
            '    top: 76px;',
            '    right: 12px;',
            '    left: 12px;',
            '    width: auto;',
            '  }',
            '}',
            '@keyframes uiToastIn {',
            '  from { opacity: 0; transform: translateY(-10px); }',
            '  to { opacity: 1; transform: translateY(0); }',
            '}',
            '.ui-dialog-mask {',
            '  position: fixed;',
            '  inset: 0;',
            '  background: rgba(0, 0, 0, 0.34);',
            '  z-index: 100000;',
            '  display: flex;',
            '  align-items: center;',
            '  justify-content: center;',
            '  padding: 20px;',
            '}',
            '.ui-dialog {',
            '  width: min(92vw, 460px);',
            '  background: #fff;',
            '  border: 1px solid #e5e7eb;',
            '  border-radius: 14px;',
            '  box-shadow: 0 10px 24px rgba(0, 0, 0, 0.18);',
            '  overflow: hidden;',
            '}',
            '.ui-dialog-head {',
            '  padding: 18px 20px 10px;',
            '  font-size: 14px;',
            '  font-weight: 700;',
            '  color: #1f2937;',
            '}',
            '.ui-dialog-body {',
            '  padding: 0 20px 16px;',
            '  color: #374151;',
            '  font-size: 13px;',
            '  line-height: 1.65;',
            '}',
            '.ui-dialog-input-wrap {',
            '  padding: 0 20px 8px;',
            '}',
            '.ui-dialog-input {',
            '  width: 100%;',
            '  border: 1px solid #d5dbe3;',
            '  border-radius: 10px;',
            '  padding: 10px 12px;',
            '  font-size: 13px;',
            '  outline: none;',
            '}',
            '.ui-dialog-input:focus {',
            '  border-color: #9aa6b2;',
            '}',
            '.ui-dialog-actions {',
            '  display: flex;',
            '  justify-content: flex-end;',
            '  gap: 10px;',
            '  padding: 14px 20px 18px;',
            '}',
            '.ui-dialog-btn {',
            '  border: 1px solid #111827;',
            '  background: #fff;',
            '  color: #111827;',
            '  border-radius: 10px;',
            '  padding: 7px 14px;',
            '  cursor: pointer;',
            '  font-size: 13px;',
            '}',
            '.ui-dialog-btn:hover {',
            '  background: #f3f4f6;',
            '}',
            '.ui-dialog-btn.primary {',
            '  background: #111827;',
            '  color: #fff;',
            '  border-color: #111827;',
            '}',
            '.ui-dialog-btn.primary:hover {',
            '  background: #000000;',
            '}',
            '.ui-dialog-btn.danger {',
            '  background: #111827;',
            '  color: #fff;',
            '  border-color: #111827;',
            '}',
            '.ui-dialog-btn.danger:hover {',
            '  background: #000000;',
            '}'
        ].join('\n');
        document.head.appendChild(style);
    }

    function ensureWrap() {
        var wrap = document.getElementById(wrapId);
        if (wrap) {
            return wrap;
        }
        wrap = document.createElement('div');
        wrap.id = wrapId;
        wrap.className = 'ui-toast-wrap';
        document.body.appendChild(wrap);
        return wrap;
    }

    function ensureDialogRoot() {
        var root = document.getElementById(dialogRootId);
        if (root) {
            return root;
        }
        root = document.createElement('div');
        root.id = dialogRootId;
        document.body.appendChild(root);
        return root;
    }

    function normalizeType(type, message) {
        if (type === 'success' || type === 'error' || type === 'info') {
            return type;
        }
        var msg = String(message || '');
        if (msg.indexOf('成功') >= 0 || msg.indexOf('完成') >= 0 || msg.indexOf('已') === 0) {
            return 'success';
        }
        return 'error';
    }

    function showToast(message, type) {
        if (!message) {
            return;
        }
        ensureStyle();
        var wrap = ensureWrap();
        var resolvedType = normalizeType(type, message);
        var icon = resolvedType === 'success' ? '\u2713' : (resolvedType === 'info' ? 'i' : '!');

        var item = document.createElement('div');
        item.className = 'ui-toast-item';
        item.innerHTML = '<span class="ui-toast-icon">' + icon + '</span><span class="ui-toast-text"></span>';
        var text = item.querySelector('.ui-toast-text');
        if (text) {
            text.textContent = String(message);
        }

        wrap.innerHTML = '';
        wrap.appendChild(item);

        window.setTimeout(function () {
            if (item && item.parentNode) {
                item.parentNode.removeChild(item);
            }
        }, resolvedType === 'error' ? 2600 : 2000);
    }

    window.showToast = showToast;

    function renderDialog(options) {
        ensureStyle();
        var root = ensureDialogRoot();
        root.innerHTML = '';

        var mask = document.createElement('div');
        mask.className = 'ui-dialog-mask';

        var dialog = document.createElement('div');
        dialog.className = 'ui-dialog';
        dialog.setAttribute('role', 'dialog');

        var title = document.createElement('div');
        title.className = 'ui-dialog-head';
        title.textContent = options.title || '请确认操作';
        dialog.appendChild(title);

        var body = document.createElement('div');
        body.className = 'ui-dialog-body';
        body.textContent = options.message || '';
        dialog.appendChild(body);

        var input = null;
        if (options.withInput) {
            var inputWrap = document.createElement('div');
            inputWrap.className = 'ui-dialog-input-wrap';
            input = document.createElement('input');
            input.className = 'ui-dialog-input';
            input.type = 'text';
            input.placeholder = options.inputPlaceholder || '';
            input.value = options.defaultValue || '';
            inputWrap.appendChild(input);
            dialog.appendChild(inputWrap);
        }

        var actions = document.createElement('div');
        actions.className = 'ui-dialog-actions';

        var cancelBtn = document.createElement('button');
        cancelBtn.className = 'ui-dialog-btn';
        cancelBtn.type = 'button';
        cancelBtn.textContent = options.cancelText || '取消';

        var okBtn = document.createElement('button');
        okBtn.className = 'ui-dialog-btn primary';
        if (options.danger) {
            okBtn.className = 'ui-dialog-btn danger';
        }
        okBtn.type = 'button';
        okBtn.textContent = options.confirmText || '确认';

        actions.appendChild(cancelBtn);
        actions.appendChild(okBtn);
        dialog.appendChild(actions);
        mask.appendChild(dialog);
        root.appendChild(mask);

        return {
            root: root,
            mask: mask,
            input: input,
            okBtn: okBtn,
            cancelBtn: cancelBtn
        };
    }

    window.showConfirm = function (message, options) {
        var opts = options || {};
        return new Promise(function (resolve) {
            var ui = renderDialog({
                title: opts.title || '请确认操作',
                message: String(message || ''),
                confirmText: opts.confirmText || '确认',
                cancelText: opts.cancelText || '取消',
                danger: Boolean(opts.danger)
            });

            function cleanup(result) {
                if (ui && ui.root) {
                    ui.root.innerHTML = '';
                }
                resolve(result);
            }

            ui.cancelBtn.addEventListener('click', function () { cleanup(false); });
            ui.okBtn.addEventListener('click', function () { cleanup(true); });
            ui.mask.addEventListener('click', function (event) {
                if (event.target === ui.mask) {
                    cleanup(false);
                }
            });

            var onKeyDown = function (event) {
                if (event.key === 'Escape') {
                    document.removeEventListener('keydown', onKeyDown);
                    cleanup(false);
                }
            };
            document.addEventListener('keydown', onKeyDown, { once: true });

            ui.okBtn.focus();
        });
    };

    window.showPrompt = function (message, defaultValue, options) {
        var opts = options || {};
        return new Promise(function (resolve) {
            var ui = renderDialog({
                title: opts.title || '请输入内容',
                message: String(message || ''),
                withInput: true,
                defaultValue: defaultValue || '',
                inputPlaceholder: opts.placeholder || '',
                confirmText: opts.confirmText || '确认',
                cancelText: opts.cancelText || '取消',
                danger: false
            });

            function cleanup(result) {
                if (ui && ui.root) {
                    ui.root.innerHTML = '';
                }
                resolve(result);
            }

            ui.cancelBtn.addEventListener('click', function () { cleanup(null); });
            ui.okBtn.addEventListener('click', function () {
                cleanup(ui.input ? ui.input.value : '');
            });
            ui.mask.addEventListener('click', function (event) {
                if (event.target === ui.mask) {
                    cleanup(null);
                }
            });
            if (ui.input) {
                ui.input.addEventListener('keydown', function (event) {
                    if (event.key === 'Enter') {
                        cleanup(ui.input.value);
                    }
                });
                ui.input.focus();
            }
        });
    };

    function createCareerAIDemoReply(message) {
        var text = String(message || '').trim().toLowerCase();
        if (!text) {
            return '你可以继续问我简历优化、行业趋势、面试模拟或者职业规划。';
        }
        if (/简历|优化|经历|项目|改写/.test(text)) {
            return '简历优化可以先抓三点：补量化成果、补岗位关键词、把项目写成“动作 + 结果”。如果你愿意，我可以继续按数据岗、产品岗或研发岗给你细拆。';
        }
        if (/趋势|行业|薪资|市场/.test(text)) {
            return '行业趋势建议重点看岗位数量变化、技能关键词变化和薪资区间变化。告诉我你关心的行业或岗位，我可以按更具体的方向继续分析。';
        }
        if (/面试|模拟|题|自我介绍/.test(text)) {
            return '面试建议按 STAR 法则准备。你可以先练“为什么投这个岗位”“最有挑战的项目是什么”“结果不理想时如何复盘”这几类题。';
        }
        if (/岗位|方向|职业规划|转行|匹配/.test(text)) {
            return '职业方向先结合专业背景、项目经历和你愿意投入学习的时间来判断。把简历重点贴给我，我可以直接帮你缩小岗位范围。';
        }
        return '我可以继续帮你看简历、分析行业、做面试题或者给职业规划建议。你也可以直接把简历内容贴给我，我会按更具体的场景回答。';
    }

    function createMockAIResponse(message) {
        var reply = createCareerAIDemoReply(message);
        return new Response(JSON.stringify({
            success: true,
            reply: reply,
            is_simulated: true,
            session_id: 'demo'
        }), {
            status: 200,
            headers: { 'Content-Type': 'application/json; charset=utf-8' }
        });
    }

    if (!window.__careerAIFetchPatched && typeof window.fetch === 'function' && window.__CAREER_AI_DEMO_MODE__) {
        window.__careerAIFetchPatched = true;
        var originalFetch = window.fetch.bind(window);
        window.fetch = function (input, init) {
            var url = '';
            if (typeof input === 'string') {
                url = input;
            } else if (input && typeof input.url === 'string') {
                url = input.url;
            }

            if (url.indexOf('/api/ai/chat') !== -1) {
                var bodyText = '';
                if (init && init.body) {
                    bodyText = typeof init.body === 'string' ? init.body : '';
                } else if (input && input.body && typeof input.body === 'string') {
                    bodyText = input.body;
                }
                var message = '';
                if (bodyText) {
                    try {
                        var parsed = JSON.parse(bodyText);
                        message = parsed.message || '';
                    } catch (error) {
                        message = bodyText;
                    }
                }
                return Promise.resolve(createMockAIResponse(message));
            }

            return originalFetch(input, init);
        };
    }

    var nativeAlert = window.alert;
    window.alert = function (message) {
        showToast(message, undefined);
    };

    window.__nativeAlert = nativeAlert;
})();
