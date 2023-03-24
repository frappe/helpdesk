import { reactive, computed } from "vue";
import { useRouter } from "vue-router";
import { defineStore } from "pinia";
import { createResource, call } from "frappe-ui";

type User = {
	hasDeskAccess: boolean;
	isAdmin: boolean;
	loading: boolean;
	username: string;
	user: string;
	agent: Record<string, any>;
};

const PATH_LOGIN = "/frappedesk/login";

export const useAuthStore = defineStore("auth", () => {
	const router = useRouter();

	const user: User = reactive({
		hasDeskAccess: false,
		isAdmin: false,
		loading: true,
		username: "",
		user: "",
		agent: null,
	});

	const userInfo = createResource({
		url: "frappedesk.api.agent.get_user",
		cache: ["LoggedAgent"],
		onSuccess(data: User) {
			Object.assign(user, data);
		},
		onError() {
			router.push({ name: "PortalLogin" });
		},
	});

	const agent = computed(() => user.agent);
	const hasDeskAccess = computed(() => user.hasDeskAccess);
	const isAdmin = computed(() => user.isAdmin);
	const userId = computed(() => user.user);

	const resLogin = createResource({
		url: "login",
	});

	const resSignup = createResource({
		url: "frappedesk.api.account.signup",
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
		call("logout").then(() => router.push({ path: PATH_LOGIN }));
	}

	function isLoggedIn() {
		const cookie = Object.fromEntries(
			document.cookie
				.split("; ")
				.map((part) => part.split("="))
				.map((d) => [d[0], decodeURIComponent(d[1])])
		);

		return cookie.user_id && cookie.user_id !== "Guest";
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
		agent,
		hasDeskAccess,
		init,
		isAdmin,
		isLoggedIn,
		login,
		logout,
		reloadUser,
		signup,
		user,
		userId,
	};
});
