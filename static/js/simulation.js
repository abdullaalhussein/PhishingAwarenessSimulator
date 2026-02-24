/**
 * PhishSim — Simulation Interactivity
 * Handles timer, stage transitions, action selection, SSE, and animations.
 */

(function () {
    'use strict';

    // ===== Elapsed Timer =====
    const TimerModule = {
        _intervalId: null,
        _startKey: null,
        _el: null,

        init(sessionId) {
            this._startKey = 'sim_start_' + sessionId;
            this._el = document.getElementById('sim-timer');
            if (!this._el) return;

            if (!sessionStorage.getItem(this._startKey)) {
                sessionStorage.setItem(this._startKey, Date.now().toString());
            }
            this._tick();
            this._intervalId = setInterval(() => this._tick(), 1000);
        },

        getElapsed() {
            const start = parseInt(sessionStorage.getItem(this._startKey), 10);
            if (!start) return 0;
            return Math.floor((Date.now() - start) / 1000);
        },

        _tick() {
            const secs = this.getElapsed();
            const m = Math.floor(secs / 60);
            const s = secs % 60;
            this._el.textContent = (m < 10 ? '0' : '') + m + ':' + (s < 10 ? '0' : '') + s;

            // Color changes based on time
            if (secs > 300) {
                this._el.classList.add('timer-slow');
                this._el.classList.remove('timer-normal');
            } else if (secs > 60) {
                this._el.classList.add('timer-normal');
            }
        },

        stop() {
            if (this._intervalId) clearInterval(this._intervalId);
        },

        cleanup(sessionId) {
            sessionStorage.removeItem('sim_start_' + sessionId);
        }
    };

    // ===== Action Card Selection =====
    const ActionModule = {
        init() {
            // Radio-based action cards
            document.querySelectorAll('.action-card').forEach(card => {
                card.addEventListener('click', function (e) {
                    // Don't interfere with checkbox clicks
                    const radio = this.querySelector('input[type="radio"]');
                    if (radio) {
                        radio.checked = true;
                        // Deselect siblings
                        document.querySelectorAll('.action-card').forEach(c => c.classList.remove('selected'));
                        this.classList.add('selected');
                    }
                });
            });

            // Checkbox-based red flag cards
            document.querySelectorAll('.flag-card').forEach(card => {
                card.addEventListener('click', function (e) {
                    if (e.target.type === 'checkbox') return; // Let native handle
                    const cb = this.querySelector('input[type="checkbox"]');
                    if (cb) {
                        cb.checked = !cb.checked;
                        this.classList.toggle('selected', cb.checked);
                    }
                });
            });
        }
    };

    // ===== Submit Confirmation =====
    const ConfirmModule = {
        init() {
            const actionForm = document.getElementById('actionForm');
            if (actionForm) {
                actionForm.addEventListener('submit', function (e) {
                    const selected = this.querySelector('input[type="radio"]:checked');
                    if (!selected) {
                        e.preventDefault();
                        shakeElement(this.querySelector('.btn-primary'));
                        return;
                    }
                    const label = selected.closest('.action-card').querySelector('.action-label');
                    if (!confirm('Are you sure you want to: "' + label.textContent.trim() + '"?')) {
                        e.preventDefault();
                    }
                });
            }

            const flagForm = document.getElementById('flagForm');
            if (flagForm) {
                flagForm.addEventListener('submit', function (e) {
                    const checked = this.querySelectorAll('input[type="checkbox"]:checked');
                    if (checked.length === 0) {
                        if (!confirm('You haven\'t selected any red flags. Are you sure you want to continue?')) {
                            e.preventDefault();
                        }
                    }
                });
            }
        }
    };

    // ===== Animated Score Reveal =====
    const ScoreModule = {
        init() {
            const circle = document.querySelector('.score-circle');
            if (!circle) return;

            const valueEl = circle.querySelector('.score-value');
            if (!valueEl) return;

            const target = parseInt(valueEl.dataset.target || valueEl.textContent, 10);
            valueEl.textContent = '0%';

            // Animate after a short delay
            setTimeout(() => {
                this._animateCount(valueEl, 0, target, 1200);
            }, 300);
        },

        _animateCount(el, from, to, duration) {
            const start = performance.now();
            const step = (timestamp) => {
                const progress = Math.min((timestamp - start) / duration, 1);
                // Ease out cubic
                const eased = 1 - Math.pow(1 - progress, 3);
                el.textContent = Math.round(from + (to - from) * eased) + '%';
                if (progress < 1) requestAnimationFrame(step);
            };
            requestAnimationFrame(step);
        }
    };

    // ===== Stage Transitions =====
    const TransitionModule = {
        init() {
            // Fade in main content
            const content = document.querySelector('.sim-content');
            if (content) {
                content.classList.add('fade-in');
            }
        }
    };

    // ===== SSE (Server-Sent Events) =====
    const SSEModule = {
        _source: null,

        init(sessionId) {
            if (!window.EventSource) return;

            const url = '/simulate/session/' + sessionId + '/stream';
            this._source = new EventSource(url);

            this._source.addEventListener('stage_change', function (e) {
                const data = JSON.parse(e.data);
                // Update progress indicators
                document.querySelectorAll('.progress-stage').forEach(stage => {
                    const stageNum = stage.dataset.stage;
                    if (stageNum && parseInt(stageNum) < data.current_stage) {
                        stage.classList.add('done');
                        stage.classList.remove('active');
                    } else if (stageNum && parseInt(stageNum) === data.current_stage) {
                        stage.classList.add('active');
                        stage.classList.remove('done');
                    }
                });
            });

            this._source.addEventListener('feedback', function (e) {
                const data = JSON.parse(e.data);
                showToast(data.message, data.type || 'info');
            });

            this._source.onerror = function () {
                // Silently close — SSE is an enhancement, not required
                this.close();
            };
        },

        close() {
            if (this._source) this._source.close();
        }
    };

    // ===== Utility Functions =====
    function shakeElement(el) {
        if (!el) return;
        el.classList.add('shake');
        setTimeout(() => el.classList.remove('shake'), 600);
    }

    function showToast(message, type) {
        const container = document.getElementById('toast-container');
        if (!container) return;

        const toast = document.createElement('div');
        toast.className = 'toast-notification toast-' + type;
        toast.textContent = message;
        container.appendChild(toast);

        setTimeout(() => toast.classList.add('show'), 10);
        setTimeout(() => {
            toast.classList.remove('show');
            setTimeout(() => toast.remove(), 300);
        }, 4000);
    }

    // ===== Initialize =====
    document.addEventListener('DOMContentLoaded', function () {
        const simContainer = document.getElementById('sim-container');
        if (!simContainer) return;

        const sessionId = simContainer.dataset.sessionId;

        TimerModule.init(sessionId);
        ActionModule.init();
        ConfirmModule.init();
        ScoreModule.init();
        TransitionModule.init();

        // SSE only on active simulation pages
        if (simContainer.dataset.stage && simContainer.dataset.stage !== 'result') {
            SSEModule.init(sessionId);
        }

        // Cleanup timer on result page
        if (simContainer.dataset.stage === 'result') {
            TimerModule.cleanup(sessionId);
        }
    });

    // Expose for external use
    window.PhishSim = { TimerModule, SSEModule };
})();
