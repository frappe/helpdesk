<div align="center" markdown="1">
<img src="https://user-images.githubusercontent.com/46772424/179259061-000ac01a-4cb5-4d99-adab-2d5951f0ca15.svg" alt="FrappeDesk logo" width="170"/>

**Open Source Helpdesk** </br>
[frappedesk.com](https://frappedesk.com)
</div>

---


FrappeDesk offers an easy setup, clean user interface, and automation tools to resolve customer issues efficiently. It is based on Frappe Framework. It lets you streamline your company's support and helps you to efficiently manage your customer queries. It can help you to,

- Create tickets from email or help center
- Empower customers with a comprehensive knowledge base and self-service portal
- Automate redundant tasks like agent assignment and set up triggers to notify agents and customers based on certain events

<img src="https://user-images.githubusercontent.com/46772424/180410739-a64b8b65-43b4-4ec8-8a87-1f5e97f355e0.png" width="">

## Installation

### Local

To setup the repository locally follow the steps mentioned below:

1. Install bench and setup a `frappe-bench` directory by following the [Installation Steps](https://frappeframework.com/docs/user/en/installation)
1. Start the server by running `bench start`
1. In a separate terminal window, create a new site by running `bench new-site frappedesk.test`
1. Map your site to localhost with the command `bench --site frappedesk.test add-to-hosts`
1. Get the Frappe Desk app. Run `bench get-app https://github.com/frappe/desk`
1. Run `bench --site frappedesk.test install-app frappedesk`.
1. Now open the URL `http://frappedesk.test:8000/frappedesk` in your browser, you should see the app running

## Contributions and Community

There are many ways you can contribute even if you don't code:

1. You can start by giving a star to this repository!
2. If you find any issues, even if it is a typo, you can [raise an issue](https://github.com/frappe/desk/issues/new) to inform us.
3. You can join our [telegram group](https://t.me/frappedesk) and share your thoughts.

## License
[GNU Affero General Public License v3.0](https://github.com/frappe/desk/blob/main/licence.md)
