/**
 * Helpdesk Login Page - Interactive Controller
 * Sprint 4: MFA OTP grid, server-driven lockout, view management
 * ~400 lines, vanilla ES module, no framework dependencies
 */

const STATES = ['sign-in', 'mfa-otp', 'forgot', 'reset-success', 'locked-out'];
const LOCKOUT_CHECK_INTERVAL = 100; // ms

/**
 * Main controller - boots on DOMContentLoaded
 */
function LoginController(root) {
	// State
	const state = {
		view: 'sign-in',
		tmpId: null,
		mfaMethod: null,
		lockoutUntil: null,
		lastEmail: '',
		resendCooldownUntil: null
	};

	// DOM refs (read once)
	const $ = {
		signInForm: root.querySelector('#sign-in-form'),
		emailInput: root.querySelector('#email'),
		passwordInput: root.querySelector('#password'),
		passwordToggle: root.querySelector('.hd-login__password-toggle'),
		forgotLink: root.querySelector('#forgot-link'),
		forgotBackBtn: root.querySelector('#forgot-back-btn'),
		forgotForm: root.querySelector('#forgot-form'),
		resetEmailInput: root.querySelector('#reset-email'),
		backToLoginBtn: root.querySelector('#back-to-login'),

		mfaBackBtn: root.querySelector('#mfa-back-btn'),
		mfaForm: root.querySelector('#mfa-form'),
		mfaPrompt: root.querySelector('#mfa-prompt'),
		otpCells: root.querySelectorAll('.hd-login__otp-cell'),
		resendOtpBtn: root.querySelector('#resend-otp'),

		lockoutCountdown: root.querySelector('#lockout-countdown'),
		lockoutResetLink: root.querySelector('#lockout-reset-link'),

		authError: root.querySelector('#auth-error'),
		otpError: root.querySelector('#otp-error'),
		resetError: root.querySelector('#reset-error')
	};

	const i18n = window.hdLoginI18n || {};

	// Render: set active view
	function setView(name) {
		if (!STATES.includes(name)) throw new Error(`Unknown view: ${name}`);
		const previousView = state.view;
		state.view = name;

		// Hide all views
		root.querySelectorAll('.hd-login__view').forEach(el => {
			el.style.display = 'none';
		});

		// Show active view
		const activeView = root.querySelector(`.hd-login__view[data-view-name="${name}"]`);
		if (activeView) {
			activeView.style.display = 'block';

			// Focus first input or button
			const focusTarget = activeView.querySelector('input:not(:disabled), button:not(:disabled)');
			if (focusTarget) {
				setTimeout(() => focusTarget.focus(), 50);
			}
		}

		// Clear errors when switching views
		clearError($.authError);
		clearError($.otpError);
		clearError($.resetError);

		// Track view switch (telemetry)
		if (window.hdTelemetry && previousView !== name) {
			window.hdTelemetry.trackViewSwitch(previousView, name);
		}
	}

	// HTTPS guard
	function checkHttps() {
		if (location.protocol !== 'https:' &&
		    !['localhost', '127.0.0.1'].some(h => location.hostname.includes(h))) {
			showError($.authError, i18n.httpsRequired || 'HTTPS required');
			return false;
		}
		return true;
	}

	// CSRF token helper
	function getCsrfToken() {
		const meta = document.querySelector('meta[name="csrf-token"]');
		return meta ? meta.content : '';
	}

	// POST helper
	async function postForm(url, body) {
		const formData = new URLSearchParams(body);
		const res = await fetch(url, {
			method: 'POST',
			headers: {
				'Content-Type': 'application/x-www-form-urlencoded',
				'X-Frappe-CSRF-Token': getCsrfToken(),
				'Accept': 'application/json',
			},
			body: formData,
			credentials: 'same-origin',
		});

		let data = null;
		const contentType = res.headers.get('content-type');
		if (contentType && contentType.includes('json')) {
			data = await res.json();
		}

		return { res, data };
	}

	// Safe redirect (server-trusted only)
	function safeRedirect(url) {
		if (!url) url = '/helpdesk';

		// Only allow same-origin redirects
		try {
			const target = new URL(url, location.origin);
			if (target.origin === location.origin) {
				window.location.href = target.href;
			} else {
				window.location.href = '/helpdesk';
			}
		} catch {
			window.location.href = '/helpdesk';
		}
	}

	// Error display helpers
	function showError(el, message) {
		if (el) {
			el.textContent = message;
			el.style.display = 'block';
		}
	}

	function clearError(el) {
		if (el) {
			el.textContent = '';
			el.style.display = 'none';
		}
	}

	// Loading state for buttons with enhanced animation
	function setButtonLoading(btn, loading) {
		if (!btn) return;

		if (loading) {
			btn.classList.add('hd-login__btn--loading');
			btn.disabled = true;
			const spinner = btn.querySelector('.hd-login__spinner');
			if (spinner) spinner.style.display = 'block';

			// Add pulse animation to the card
			const card = document.querySelector('.hd-login__card');
			if (card) card.classList.add('hd-login__card--authenticating');
		} else {
			btn.classList.remove('hd-login__btn--loading');
			btn.disabled = false;
			const spinner = btn.querySelector('.hd-login__spinner');
			if (spinner) spinner.style.display = 'none';

			// Remove pulse animation from the card
			const card = document.querySelector('.hd-login__card');
			if (card) card.classList.remove('hd-login__card--authenticating');
		}
	}

	// Lockout countdown
	function startLockoutCountdown() {
		if (!state.lockoutUntil) return;

		const update = () => {
			const now = Date.now();
			const remaining = Math.max(0, Math.ceil((state.lockoutUntil - now) / 1000));

			if ($.lockoutCountdown) {
				$.lockoutCountdown.textContent = String(remaining);
			}

			if (remaining <= 0) {
				// Lockout expired, return to sign-in
				state.lockoutUntil = null;
				setView('sign-in');
			} else {
				requestAnimationFrame(update);
			}
		};

		requestAnimationFrame(update);
	}

	// Parse Retry-After from response
	function parseRetryAfter(res) {
		const retryAfter = res.headers.get('Retry-After');
		if (retryAfter) {
			const seconds = parseInt(retryAfter, 10);
			if (!isNaN(seconds) && seconds > 0) {
				return seconds * 1000; // convert to ms
			}
		}
		return null;
	}

	// Check if response indicates lockout
	function checkLockout(res, data) {
		const retryMs = parseRetryAfter(res);
		if (retryMs) {
			state.lockoutUntil = Date.now() + retryMs;
			setView('locked-out');
			startLockoutCountdown();
			return true;
		}

		// Also check for Frappe's LoginAttemptTracker message
		if (data && data.exc && typeof data.exc === 'string') {
			if (data.exc.includes('locked') || data.exc.includes('resume after')) {
				state.lockoutUntil = Date.now() + 30000; // 30s fallback
				setView('locked-out');
				startLockoutCountdown();
				return true;
			}
		}

		return false;
	}

	// ===== Sign In Handler =====
	async function onSignInSubmit(e) {
		e.preventDefault();
		if (!checkHttps()) return;

		clearError($.authError);

		const email = $.emailInput.value.trim();
		const password = $.passwordInput.value;
		const rememberMe = root.querySelector('input[name="remember_me"]').checked;

		if (!email || !password) {
			showError($.authError, i18n.incorrectCredentials || 'Email or password is incorrect.');
			return;
		}

		state.lastEmail = email;

		const submitBtn = $.signInForm.querySelector('button[type="submit"]');
		setButtonLoading(submitBtn, true);

		try {
			const { res, data } = await postForm('/api/method/login', {
				usr: email,
				pwd: password,
				...(rememberMe && { remember_me: 1 })
			});

			setButtonLoading(submitBtn, false);

			// Check for lockout first
			if (checkLockout(res, data)) return;

			if (res.ok && data) {
				// Check for MFA requirement
				if (data.message && data.message.verification && data.message.tmp_id) {
					state.tmpId = data.message.tmp_id;
					state.mfaMethod = data.message.verification.method || 'OTP App';

					// Update MFA prompt based on method
					if ($.mfaPrompt) {
						if (state.mfaMethod.toLowerCase().includes('email')) {
							$.mfaPrompt.textContent = i18n.emailOtpPrompt || 'Enter the 6-digit code we just emailed you';
							if ($.resendOtpBtn) $.resendOtpBtn.style.display = 'block';
						} else {
							$.mfaPrompt.textContent = i18n.totpPrompt || 'Enter the 6-digit code from your authenticator app';
							if ($.resendOtpBtn) $.resendOtpBtn.style.display = 'none';
						}
					}

					setView('mfa-otp');
					return;
				}

				// Success - redirect
				const redirectTo = (data.message && data.message.redirect_to) || '/helpdesk';
				safeRedirect(redirectTo);
			} else {
				// Failed auth
				showError($.authError, i18n.incorrectCredentials || 'Email or password is incorrect.');
			}
		} catch (err) {
			setButtonLoading(submitBtn, false);
			showError($.authError, i18n.networkError || 'Something went wrong. Please try again.');
			console.error('Login error:', err);
		}
	}

	// ===== OTP Grid Handlers =====
	function initOtpGrid() {
		const cells = Array.from($.otpCells);

		// Auto-advance on input
		cells.forEach((cell, idx) => {
			cell.addEventListener('input', (e) => {
				const val = e.target.value;

				// Only allow digits
				if (!/^\d*$/.test(val)) {
					e.target.value = '';
					return;
				}

				// Auto-advance to next cell
				if (val.length === 1 && idx < cells.length - 1) {
					cells[idx + 1].focus();
				}

				// Auto-submit when all cells filled
				if (idx === cells.length - 1 && val.length === 1) {
					const allFilled = cells.every(c => c.value.length === 1);
					if (allFilled) {
						submitOtp();
					}
				}
			});

			// Backspace handling
			cell.addEventListener('keydown', (e) => {
				if (e.key === 'Backspace' && !e.target.value && idx > 0) {
					cells[idx - 1].focus();
					cells[idx - 1].value = '';
				}

				// Arrow key navigation
				if (e.key === 'ArrowLeft' && idx > 0) {
					e.preventDefault();
					cells[idx - 1].focus();
				}
				if (e.key === 'ArrowRight' && idx < cells.length - 1) {
					e.preventDefault();
					cells[idx + 1].focus();
				}
			});

			// Paste handling
			cell.addEventListener('paste', (e) => {
				e.preventDefault();
				const pastedData = e.clipboardData.getData('text').trim();
				const digits = pastedData.replace(/\D/g, '').slice(0, 6);

				if (digits.length === 6) {
					digits.split('').forEach((digit, i) => {
						if (cells[i]) cells[i].value = digit;
					});
					cells[5].focus();
					submitOtp();
				}
			});
		});
	}

	function clearOtpCells() {
		$.otpCells.forEach(cell => {
			cell.value = '';
			cell.disabled = false;
		});
		if ($.otpCells[0]) $.otpCells[0].focus();
	}

	async function submitOtp() {
		clearError($.otpError);

		const otp = Array.from($.otpCells).map(c => c.value).join('');
		if (otp.length !== 6 || !state.tmpId) return;

		// Disable cells during submission
		$.otpCells.forEach(cell => cell.disabled = true);

		try {
			const { res, data } = await postForm('/api/method/login', {
				usr: state.lastEmail,
				pwd: '', // Not needed for OTP step but Frappe may expect it
				otp: otp,
				tmp_id: state.tmpId
			});

			// Check for lockout
			if (checkLockout(res, data)) {
				clearOtpCells();
				return;
			}

			if (res.ok && data && data.message) {
				// OTP success - redirect
				const redirectTo = data.message.redirect_to || '/helpdesk';
				safeRedirect(redirectTo);
			} else {
				// OTP failed
				showError($.otpError, i18n.otpIncorrect || "That code didn't work. Try again.");
				clearOtpCells();
			}
		} catch (err) {
			showError($.otpError, i18n.networkError || 'Something went wrong. Please try again.');
			clearOtpCells();
			console.error('OTP error:', err);
		}
	}

	// Resend OTP
	async function onResendOtp() {
		if (state.resendCooldownUntil && Date.now() < state.resendCooldownUntil) {
			return; // Still in cooldown
		}

		if ($.resendOtpBtn) {
			$.resendOtpBtn.disabled = true;
			$.resendOtpBtn.textContent = 'Sending...';
		}

		try {
			// Re-trigger login to get a new OTP
			await postForm('/api/method/login', {
				usr: state.lastEmail,
				pwd: '' // Frappe may cache the original password for resend
			});

			// Set 30s cooldown
			state.resendCooldownUntil = Date.now() + 30000;

			if ($.resendOtpBtn) {
				let countdown = 30;
				const interval = setInterval(() => {
					countdown--;
					if (countdown <= 0) {
						clearInterval(interval);
						$.resendOtpBtn.disabled = false;
						$.resendOtpBtn.textContent = i18n.resendCode || 'Resend code';
						state.resendCooldownUntil = null;
					} else {
						$.resendOtpBtn.textContent = `Resend (${countdown}s)`;
					}
				}, 1000);
			}
		} catch (err) {
			if ($.resendOtpBtn) {
				$.resendOtpBtn.disabled = false;
				$.resendOtpBtn.textContent = i18n.resendCode || 'Resend code';
			}
			console.error('Resend OTP error:', err);
		}
	}

	// ===== Forgot Password Handler =====
	async function onForgotSubmit(e) {
		e.preventDefault();
		clearError($.resetError);

		const email = $.resetEmailInput.value.trim();
		if (!email) {
			showError($.resetError, 'Please enter your email address.');
			return;
		}

		const submitBtn = $.forgotForm.querySelector('button[type="submit"]');
		setButtonLoading(submitBtn, true);

		try {
			await postForm('/api/method/frappe.core.doctype.user.user.reset_password', {
				user: email
			});

			// Always show success (privacy-preserving)
			setButtonLoading(submitBtn, false);
			setView('reset-success');
		} catch (err) {
			// Even on error, show success to prevent enumeration
			setButtonLoading(submitBtn, false);
			setView('reset-success');
		}
	}

	// ===== Password Toggle =====
	function onPasswordToggle() {
		if (!$.passwordInput || !$.passwordToggle) return;

		const isPassword = $.passwordInput.type === 'password';
		$.passwordInput.type = isPassword ? 'text' : 'password';
		$.passwordToggle.setAttribute('aria-pressed', String(!isPassword));
		$.passwordToggle.setAttribute('aria-label',
			isPassword ? (i18n.hidePassword || 'Hide password') : (i18n.showPassword || 'Show password')
		);

		// Track password toggle (telemetry)
		if (window.hdTelemetry) {
			window.hdTelemetry.trackPasswordToggle(!isPassword);
		}
	}

	// ===== Event Listeners =====
	if ($.signInForm) {
		$.signInForm.addEventListener('submit', onSignInSubmit);
	}

	if ($.passwordToggle) {
		$.passwordToggle.addEventListener('click', onPasswordToggle);
	}

	if ($.forgotLink) {
		$.forgotLink.addEventListener('click', (e) => {
			e.preventDefault();
			// Preserve email
			if ($.resetEmailInput && $.emailInput) {
				$.resetEmailInput.value = $.emailInput.value;
			}
			// Track forgot password click (telemetry)
			if (window.hdTelemetry) {
				window.hdTelemetry.trackForgotPassword('clicked');
			}
			setView('forgot');
		});
	}

	if ($.forgotBackBtn) {
		$.forgotBackBtn.addEventListener('click', () => setView('sign-in'));
	}

	if ($.forgotForm) {
		$.forgotForm.addEventListener('submit', onForgotSubmit);
	}

	if ($.backToLoginBtn) {
		$.backToLoginBtn.addEventListener('click', () => setView('sign-in'));
	}

	if ($.mfaBackBtn) {
		$.mfaBackBtn.addEventListener('click', () => {
			state.tmpId = null;
			state.mfaMethod = null;
			clearOtpCells();
			setView('sign-in');
		});
	}

	if ($.resendOtpBtn) {
		$.resendOtpBtn.addEventListener('click', onResendOtp);
	}

	if ($.lockoutResetLink) {
		$.lockoutResetLink.addEventListener('click', (e) => {
			e.preventDefault();
			state.lockoutUntil = null;
			setView('forgot');
		});
	}

	// Init OTP grid
	if ($.otpCells.length > 0) {
		initOtpGrid();
	}

	// Check for password_reset query param
	const params = new URLSearchParams(location.search);
	if (params.get('password_reset') === '1') {
		const banner = document.createElement('div');
		banner.className = 'hd-login__success-banner';
		banner.setAttribute('role', 'status');
		banner.textContent = 'Password updated. Please sign in.';
		banner.style.cssText = `
			background: #D1FAE5;
			color: #065F46;
			padding: 12px;
			text-align: center;
			font-size: 14px;
			font-weight: 500;
			border-radius: 8px;
			margin-bottom: 16px;
		`;
		$.signInForm.insertAdjacentElement('beforebegin', banner);

		// Auto-dismiss after 8s
		setTimeout(() => banner.remove(), 8000);
	}

	// Initial view
	setView('sign-in');
}

// Boot on DOMContentLoaded
document.addEventListener('DOMContentLoaded', () => {
	const root = document.querySelector('.hd-login');
	if (root) {
		LoginController(root);
	}
});
