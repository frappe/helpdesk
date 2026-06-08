/**
 * Login Page Telemetry - Sprint 7
 * Privacy-safe event tracking with PostHog
 * Whitelist approach: only explicitly allowed events are tracked
 */

const TELEMETRY_ENABLED = window.hdLoginTelemetry?.enabled || false;
const POSTHOG_KEY = window.hdLoginTelemetry?.posthogKey || null;
const POSTHOG_HOST = window.hdLoginTelemetry?.posthogHost || 'https://app.posthog.com';

// Event whitelist - only these events can be tracked
const ALLOWED_EVENTS = [
	'login_page_viewed',
	'login_form_submitted',
	'login_success',
	'login_failed',
	'mfa_required',
	'mfa_code_submitted',
	'mfa_success',
	'mfa_failed',
	'forgot_password_clicked',
	'forgot_password_submitted',
	'password_toggle_clicked',
	'lockout_triggered',
	'view_switched',
	'resend_otp_clicked',
];

// Property whitelist - only these properties can be tracked
const ALLOWED_PROPERTIES = [
	'view_name',           // Current view (sign-in, mfa-otp, etc.)
	'mfa_method',          // OTP method (email, totp)
	'error_type',          // Error category (auth, network, validation)
	'brand_name',          // Tenant brand name
	'https_enabled',       // Whether HTTPS is used
	'remember_me',         // Remember me checkbox state
	'has_lockout',         // Whether lockout occurred
	'browser',             // Browser name (from user agent)
	'viewport_width',      // Screen width category (mobile/tablet/desktop)
	'password_visible',    // Whether password is shown
];

let posthog = null;
let isInitialized = false;

/**
 * Initialize PostHog if enabled
 */
function initTelemetry() {
	if (!TELEMETRY_ENABLED || !POSTHOG_KEY || isInitialized) {
		return;
	}

	// Load PostHog from CDN
	const script = document.createElement('script');
	script.src = 'https://cdn.posthog.com/array.js';
	script.async = true;
	script.onload = () => {
		if (window.posthog) {
			window.posthog.init(POSTHOG_KEY, {
				api_host: POSTHOG_HOST,
				loaded: (ph) => {
					posthog = ph;
					isInitialized = true;
					console.log('[Telemetry] PostHog initialized');
				},
				// Privacy settings
				persistence: 'localStorage',
				disable_session_recording: true,
				disable_surveys: true,
				autocapture: false,  // Manual events only
				capture_pageview: false,  // Manual pageview tracking
				mask_all_text: true,
				mask_all_element_attributes: true,
			});
		}
	};
	document.head.appendChild(script);
}

/**
 * Track an event (whitelist enforced)
 * @param {string} eventName - Event name (must be in ALLOWED_EVENTS)
 * @param {object} properties - Event properties (keys must be in ALLOWED_PROPERTIES)
 */
function trackEvent(eventName, properties = {}) {
	// Check if telemetry is enabled
	if (!TELEMETRY_ENABLED || !isInitialized || !posthog) {
		return;
	}

	// Enforce event whitelist
	if (!ALLOWED_EVENTS.includes(eventName)) {
		console.warn(`[Telemetry] Event "${eventName}" not in whitelist. Skipping.`);
		return;
	}

	// Enforce property whitelist
	const filteredProperties = {};
	for (const [key, value] of Object.entries(properties)) {
		if (ALLOWED_PROPERTIES.includes(key)) {
			filteredProperties[key] = value;
		} else {
			console.warn(`[Telemetry] Property "${key}" not in whitelist. Skipping.`);
		}
	}

	// Add base context
	const context = {
		...filteredProperties,
		browser: getBrowserName(),
		viewport_width: getViewportCategory(),
		timestamp: new Date().toISOString(),
	};

	// Track event
	posthog.capture(eventName, context);
	console.log(`[Telemetry] Event tracked: ${eventName}`, context);
}

/**
 * Get browser name from user agent
 */
function getBrowserName() {
	const ua = navigator.userAgent;
	if (ua.includes('Firefox')) return 'Firefox';
	if (ua.includes('Edg')) return 'Edge';
	if (ua.includes('Chrome')) return 'Chrome';
	if (ua.includes('Safari')) return 'Safari';
	return 'Other';
}

/**
 * Get viewport size category
 */
function getViewportCategory() {
	const width = window.innerWidth;
	if (width < 768) return 'mobile';
	if (width < 1024) return 'tablet';
	return 'desktop';
}

/**
 * Track page view
 */
function trackPageView(viewName, brandName = null) {
	trackEvent('login_page_viewed', {
		view_name: viewName,
		brand_name: brandName,
		https_enabled: location.protocol === 'https:',
	});
}

/**
 * Track view switch
 */
function trackViewSwitch(fromView, toView) {
	trackEvent('view_switched', {
		view_name: toView,
	});
}

/**
 * Track login submission
 */
function trackLoginSubmit(rememberMe = false) {
	trackEvent('login_form_submitted', {
		remember_me: rememberMe,
		https_enabled: location.protocol === 'https:',
	});
}

/**
 * Track login result
 */
function trackLoginResult(success, errorType = null) {
	if (success) {
		trackEvent('login_success', {});
	} else {
		trackEvent('login_failed', {
			error_type: errorType || 'unknown',
		});
	}
}

/**
 * Track MFA required
 */
function trackMFARequired(method) {
	trackEvent('mfa_required', {
		mfa_method: method,
	});
}

/**
 * Track MFA submission
 */
function trackMFASubmit() {
	trackEvent('mfa_code_submitted', {});
}

/**
 * Track MFA result
 */
function trackMFAResult(success) {
	if (success) {
		trackEvent('mfa_success', {});
	} else {
		trackEvent('mfa_failed', {});
	}
}

/**
 * Track forgot password flow
 */
function trackForgotPassword(step) {
	if (step === 'clicked') {
		trackEvent('forgot_password_clicked', {});
	} else if (step === 'submitted') {
		trackEvent('forgot_password_submitted', {});
	}
}

/**
 * Track lockout
 */
function trackLockout() {
	trackEvent('lockout_triggered', {
		has_lockout: true,
	});
}

/**
 * Track password toggle
 */
function trackPasswordToggle(visible) {
	trackEvent('password_toggle_clicked', {
		password_visible: visible,
	});
}

/**
 * Track resend OTP
 */
function trackResendOTP() {
	trackEvent('resend_otp_clicked', {});
}

// Export telemetry functions
window.hdTelemetry = {
	init: initTelemetry,
	trackEvent,
	trackPageView,
	trackViewSwitch,
	trackLoginSubmit,
	trackLoginResult,
	trackMFARequired,
	trackMFASubmit,
	trackMFAResult,
	trackForgotPassword,
	trackLockout,
	trackPasswordToggle,
	trackResendOTP,
};

// Auto-initialize on load
if (document.readyState === 'loading') {
	document.addEventListener('DOMContentLoaded', initTelemetry);
} else {
	initTelemetry();
}
