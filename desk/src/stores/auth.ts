import { computed, ComputedRef } from "vue";
import { useRouter } from "vue-router";
import { defineStore } from "pinia";
import { isEmpty } from "lodash";
import { createResource, call } from "frappe-ui";

const VIEW_LOGIN = "Login";
const URI_USER_INFO = "helpdesk.api.auth.get_user";
const URI_SIGNUP = "helpdesk.api.account.signup";
const URI_LOGIN = "login";

export const useAuthStore = defineStore("auth", () => {
	const router = useRouter();

	const userInfo = createResource({
		url: URI_USER_INFO,
		onError() {
			router.push({ name: VIEW_LOGIN });
		},
	});

	const user__ = computed(() => userInfo.data || {});
	const hasDeskAccess: ComputedRef<boolean> = computed(
		() => user__.value.has_desk_access
	);
	const isAdmin: ComputedRef<boolean> = computed(() => user__.value.is_admin);
	const isAgent: ComputedRef<boolean> = computed(() => user__.value.is_agent);
	const isLoggedIn: ComputedRef<boolean> = computed(
		() => !isEmpty(user__.value)
	);
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
		call("logout").then(() => router.push({ name: VIEW_LOGIN }));
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
		isAgent,
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
