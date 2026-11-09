(() => {
	const statusUrl = document.body.dataset.readyOrdersUrl;
	const countBadges = document.querySelectorAll('[data-ready-count]');
	const orderList = document.querySelector('#readyOrders');
	const readyLink = document.querySelector('.notification-bell') || document.querySelector('.ready-orders-link');
	const readyPageUrl = readyLink ? readyLink.href : '/pedidos/prontos/';
	const seenStorageKey = 'sabor-tech-ready-order-ids';
	let seenReadyIds = new Set();
	let initialized = false;
	let toastTimer;

	try {
		seenReadyIds = new Set(JSON.parse(sessionStorage.getItem(seenStorageKey) || '[]').map(String));
	} catch {
		seenReadyIds = new Set();
	}

	function showToast() {
		let toast = document.querySelector('.ready-notification-toast');
		if (!toast) {
			toast = document.createElement('div');
			toast.className = 'ready-notification-toast';
			toast.setAttribute('role', 'status');
			toast.setAttribute('aria-live', 'polite');
			document.body.append(toast);
		}

		toast.replaceChildren();
		const message = document.createElement('span');
		message.textContent = 'Novo pedido pronto para retirada.';
		const link = document.createElement('a');
		link.href = readyPageUrl;
		link.textContent = 'Ver pedidos';
		const close = document.createElement('button');
		close.type = 'button';
		close.setAttribute('aria-label', 'Fechar notificação');
		close.textContent = '×';
		close.addEventListener('click', () => { toast.hidden = true; });
		toast.append(message, link, close);
		toast.hidden = false;
		window.clearTimeout(toastTimer);
		toastTimer = window.setTimeout(() => { toast.hidden = true; }, 7000);
	}

	async function refreshReadyOrders() {
		if (!statusUrl) return;
		try {
			const response = await fetch(statusUrl, {
				headers: { Accept: 'application/json' },
				cache: 'no-store',
				credentials: 'same-origin',
			});
			if (!response.ok) return;
			const data = await response.json();
			const count = Number(data.ready_count) || 0;
			countBadges.forEach((badge) => {
				badge.textContent = String(count);
				badge.hidden = count === 0;
			});

			const currentReadyIds = new Set(
				data.orders.filter((order) => order.status === 'Pronto').map((order) => String(order.id)),
			);
			const hasNewOrder = initialized && [...currentReadyIds].some((id) => !seenReadyIds.has(id));
			if (hasNewOrder) showToast();
			currentReadyIds.forEach((id) => seenReadyIds.add(id));
			try {
				sessionStorage.setItem(seenStorageKey, JSON.stringify([...seenReadyIds]));
			} catch {
				// Notifications still work for the current page if storage is unavailable.
			}
			initialized = true;

			if (orderList) orderList.innerHTML = data.html;
		} catch {
			// Keep the last known count if a polling request is temporarily unavailable.
		}
	}

	refreshReadyOrders();
	window.setInterval(refreshReadyOrders, 5000);
})();
