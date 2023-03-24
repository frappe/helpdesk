import { computed, ComputedRef } from "vue";
import { useRouter } from "vue-router";
import { defineStore } from "pinia";
import { createResource, call } from "frappe-ui";

const REDIRECT_LOGIN = "/frappedesk/login";
const URI_USER_INFO = "frappedesk.api.auth.get_user";
const URI_SIGNUP = "frappedesk.api.account.signup";
const URI_LOGIN = "login";

export const useAuthStore = defineStore("auth", () => {
	const router = useRouter();

	const userInfo = createResource({
		url: URI_USER_INFO,
		cache: ["LoggedAgent"],
		onError() {
			router.push({ name: "PortalLogin" });
		},
	});

	const user__ = computed(() => userInfo.data);
	const hasDeskAccess: ComputedRef<boolean> = computed(
		() => user__.value.has_desk_access
	);
	const isAdmin: ComputedRef<boolean> = computed(() => user__.value.is_admin);
	const isLoggedIn: ComputedRef<boolean> = computed(() => {
		const cookie = Object.fromEntries(
			document.cookie
				.split("; ")
				.map((part) => part.split("="))
				.map((d) => [d[0], decodeURIComponent(d[1])])
		);

		return cookie.user_id && cookie.user_id !== "Guest";
	});
	const userId: ComputedRef<string> = computed(() => user__.value.user_id);
	const userImage: ComputedRef<string> = computed(
		() => user__.value.user_image
	);
	const userName: ComputedRef<string> = computed(() => user__.value.user_name);
	const username: ComputedRef<string> = computed(() => user__.value.username);

	const resLogin = createResource({
		url: URI_LOGIN,
	});

	const resSignup = createResource({
		url: URI_SIGNUP,
	});

	function signup(
		email: string,
		firstName: string,
		lastName: string,
		password: string
	) {
		return resSignup.submit({
			email,
			first_name: firstName,
			last_name: lastName,
			password,
		});
	}

	function login(email: string, password: string) {
		return resLogin.submit({
			usr: email,
			pwd: password,
		});
	}

	function logout() {
		call("logout").then(() => router.push({ path: REDIRECT_LOGIN }));
	}

	function reloadUser() {
		userInfo.reload();
	}

	/**
	 * To be called from `App.vue`
	 */
	async function init() {
		await userInfo.fetch();
	}

	return {
		hasDeskAccess,
		init,
		isAdmin,
		isLoggedIn,
		login,
		logout,
		reloadUser,
		signup,
		userId,
		userImage,
		userName,
		username,
	};
});
