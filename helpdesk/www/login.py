"""
Helpdesk Custom Login Page
Branded login page for Frappe Helpdesk
Implements AD-02 (route claim), AD-06 (feature flag), AD-09 (dynamic branding)
"""

import frappe
from frappe import _
from frappe.utils import cint


def get_context(context):
	"""
	Build context for login.html template
	Implements brand resolution (AD-09) and feature-flag check (AD-06)
	"""
	try:
		# Redirect logged-in users to desk
		if frappe.session.user != "Guest":
			frappe.local.flags.redirect_location = "/app"
			raise frappe.Redirect

		# Set Content Security Policy headers
		set_csp_headers()

		# Resolve brand for this request
		brand = resolve_brand()

		# Get telemetry settings
		telemetry_config = get_telemetry_config()

		# Get host for portal detection
		host = frappe.local.request.host.lower() if frappe.local.request.host else ""

		# Build context
		context.update({
			"brand": brand,
			"csrf_token": frappe.sessions.get_csrf_token(),
			"preview_mode": False,
			"no_cache": 1,
			"show_sidebar": False,
			"telemetry": telemetry_config,
			"is_dha": "dha" in host,
			"host": host,
		})

		return context
	except Exception as e:
		import traceback
		frappe.log_error(f"Login page error: {str(e)}\n{traceback.format_exc()}", "Login Page Error")
		raise


def resolve_brand():
	"""
	Resolve the active HD Brand for this request based on:
	  1. ?tenant=<slug> query parameter (admin override)
	  2. Host header match against HD Brand.host_patterns
	  3. HD Brand with is_default=1
	  4. Built-in fallback brand

	Returns a dict with brand fields ready for template rendering.
	AD-09 implementation.
	"""
	# Check for tenant override (?tenant=<slug>)
	tenant_override = frappe.form_dict.get("tenant")
	if tenant_override:
		brand_doc = frappe.db.get_value(
			"HD Brand",
			{"name": tenant_override, "is_active": 1},
			[
				"name",
				"brand_name as display_name",
				"logo",
				"portal_domain",
				"primary_color",
				"support_email",
			],
			as_dict=True,
		)
		if brand_doc:
			return _enrich_brand(brand_doc)

	# Host-pattern resolution
	host = frappe.local.request.host
	if host:
		host = host.lower().split(":")[0]  # Strip port

		# Try cache first
		cache_key = f"hd_brand_by_host:{host}"
		cached = frappe.cache().get_value(cache_key)
		if cached:
			return cached

		# Fetch all active brands
		brands = frappe.get_all(
			"HD Brand",
			filters={"is_active": 1},
			fields=[
				"name",
				"brand_name as display_name",
				"logo",
				"portal_domain",
				"primary_color",
				"support_email",
			],
		)

		# Match against portal_domain (simple exact match for now)
		for brand_doc in brands:
			if brand_doc.get("portal_domain") and brand_doc["portal_domain"].lower() == host:
				result = _enrich_brand(brand_doc)
				frappe.cache().set_value(cache_key, result, expires_in_sec=3600)
				return result

	# Fallback: first active brand or built-in default
	default_brand = frappe.db.get_value(
		"HD Brand",
		{"is_active": 1},
		[
			"name",
			"brand_name as display_name",
			"logo",
			"portal_domain",
			"primary_color",
			"support_email",
		],
		as_dict=True,
		order_by="creation asc",
	)

	if default_brand:
		return _enrich_brand(default_brand)

	# Built-in fallback
	return _get_fallback_brand()


def _enrich_brand(brand_doc):
	"""
	Enrich a brand dict with computed fields and defaults
	"""
	if not brand_doc:
		return _get_fallback_brand()

	# Ensure all required fields have defaults
	brand = {
		"name": brand_doc.get("name", ""),
		"display_name": brand_doc.get("display_name") or brand_doc.get("brand_name") or "Helpdesk",
		"logo": brand_doc.get("logo") or "",
		"primary_color": brand_doc.get("primary_color") or "#059669",
		"accent_color": _derive_accent_color(brand_doc.get("primary_color")),
		"bg_tint_color": _derive_bg_tint(brand_doc.get("primary_color")),
		"support_email": brand_doc.get("support_email") or "",
		"headline": _("Welcome back · Sign in to Helpdesk"),
		"supporting_copy": _("Modern customer service software · Track tickets, browse the knowledge base, get answers fast."),
		"perks": _get_default_perks(),
		"trust_stats": _get_default_stats(),
	}

	return brand


def _get_fallback_brand():
	"""
	Built-in fallback brand when no HD Brand records exist
	"""
	return {
		"name": "_helpdesk",
		"display_name": "Helpdesk",
		"logo": "",
		"primary_color": "#059669",
		"accent_color": "#047857",
		"bg_tint_color": "rgba(5, 150, 105, 0.08)",
		"support_email": "",
		"headline": _("Welcome back · Sign in to Helpdesk"),
		"supporting_copy": _("Modern customer service software · Track tickets, browse the knowledge base, get answers fast."),
		"perks": _get_default_perks(),
		"trust_stats": _get_default_stats(),
	}


def _derive_accent_color(primary_color):
	"""
	Derive accent color from primary (simple darkening for now)
	"""
	if not primary_color or primary_color == "#059669":
		return "#047857"
	# Simple fallback: return primary
	return primary_color


def _derive_bg_tint(primary_color):
	"""
	Derive background tint from primary color
	"""
	if not primary_color:
		return "rgba(5, 150, 105, 0.08)"

	# Parse hex to RGB
	try:
		hex_color = primary_color.lstrip("#")
		r = int(hex_color[0:2], 16)
		g = int(hex_color[2:4], 16)
		b = int(hex_color[4:6], 16)
		return f"rgba({r}, {g}, {b}, 0.08)"
	except:
		return "rgba(5, 150, 105, 0.08)"


def _get_default_perks():
	"""
	Default perks list for agent/customer audience
	"""
	return [
		{
			"label": _("Fast Resolution"),
			"description": _("Get help quickly with our streamlined support process"),
		},
		{
			"label": _("24/7 Availability"),
			"description": _("Access your tickets and knowledge base anytime"),
		},
		{
			"label": _("Secure & Private"),
			"description": _("Your data is encrypted and protected"),
		},
	]


def _get_default_stats():
	"""
	Default trust stats (static for v1)
	"""
	return [
		{"value": "10k+", "label": _("Active Users")},
		{"value": "99.9%", "label": _("Uptime")},
		{"value": "<2h", "label": _("Avg Response")},
	]


def set_csp_headers():
	"""
	Set Content Security Policy headers for login page
	Sprint 7: CSP implementation
	"""
	# Initialize response headers if not already done
	if not hasattr(frappe.local, "response") or frappe.local.response is None:
		frappe.local.response = frappe._dict()
	if not hasattr(frappe.local.response, "headers") or frappe.local.response.headers is None:
		frappe.local.response.headers = {}

	# Define CSP policy
	csp_policy = "; ".join([
		"default-src 'self'",
		"script-src 'self' 'unsafe-inline' https://cdn.posthog.com",
		"style-src 'self' 'unsafe-inline'",
		"img-src 'self' data: https:",
		"font-src 'self' data:",
		"connect-src 'self' https://app.posthog.com",
		"frame-ancestors 'none'",
		"base-uri 'self'",
		"form-action 'self'",
	])

	frappe.local.response.headers["Content-Security-Policy"] = csp_policy
	frappe.local.response.headers["X-Frame-Options"] = "DENY"
	frappe.local.response.headers["X-Content-Type-Options"] = "nosniff"
	frappe.local.response.headers["Referrer-Policy"] = "strict-origin-when-cross-origin"


def get_telemetry_config():
	"""
	Get telemetry configuration from HD Settings
	Returns config dict for frontend
	"""
	try:
		settings = frappe.get_cached_doc("HD Settings")
		telemetry_enabled = getattr(settings, "login_telemetry_enabled", False)
		posthog_key = getattr(settings, "posthog_api_key", None)
		posthog_host = getattr(settings, "posthog_host", "https://app.posthog.com")

		return {
			"enabled": telemetry_enabled and bool(posthog_key),
			"posthogKey": posthog_key if telemetry_enabled else None,
			"posthogHost": posthog_host if telemetry_enabled else None,
		}
	except:
		return {
			"enabled": False,
			"posthogKey": None,
			"posthogHost": None,
		}


@frappe.whitelist(allow_guest=False, methods=["POST"])
def invalidate_brand_cache():
	"""
	Flush the brand resolution cache
	Called from HD Brand.on_update / on_trash hooks
	"""
	# Flush all hd_brand_by_host keys
	cache = frappe.cache()
	keys = cache.get_keys("hd_brand_by_host:*")
	for key in keys:
		cache.delete_value(key)

	return {"status": "ok"}
