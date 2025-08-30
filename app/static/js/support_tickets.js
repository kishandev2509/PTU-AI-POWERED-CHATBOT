document.addEventListener("DOMContentLoaded", function () {
	// Get CSRF token
	const csrfToken = document.querySelector('meta[name="csrf-token"]').getAttribute("content");

	// Initialize tooltips
	const tooltips = document.querySelectorAll("[title]");
	tooltips.forEach((tooltip) => {
		new bootstrap.Tooltip(tooltip);
	});

	// Handle view switching
	const views = {
		inbox: document.getElementById("inboxView"),
		sent: document.getElementById("sentView"),
		starred: document.getElementById("starredView"),
		archive: document.getElementById("archiveView"),
		trash: document.getElementById("trashView"),
	};

	// Setup query item listeners for all current and future items
	function setupQueryItemListeners(item) {
		const queryId = item.getAttribute("data-id");
		// Star button
		const starBtn = item.querySelector(".star-btn");
		if (starBtn) {
			starBtn.addEventListener("click", (e) => {
				e.stopPropagation();
				toggleStar(queryId);
			});
		}
		// Delete button
		const deleteBtn = item.querySelector(".delete-btn");
		if (deleteBtn) {
			deleteBtn.addEventListener("click", (e) => {
				e.stopPropagation();
				deleteQuery(queryId, isTrashView);
			});
		}
		// Archive button
		const archiveBtn = item.querySelector(".archive-btn");
		if (archiveBtn) {
			archiveBtn.addEventListener("click", (e) => {
				e.stopPropagation();
				toggleArchive(queryId);
			});
		}
		const restoreBtn = item.querySelector(".restore-btn");
		if (restoreBtn) {
			restoreBtn.addEventListener("click", (e) => {
				e.stopPropagation();
				restoreQuery(queryId);
			});
		}
		// Click to view
		item.addEventListener("click", (e) => {
			if (!e.target.closest(".query-actions")) {
				viewQuery(queryId);
			}
		});
	}
	// Attach listeners to all existing query items in all views
	document.querySelectorAll(".query-item").forEach(setupQueryItemListeners);

	// Add error handling and notifications
	function showNotification(message, type = "success") {
		const notification = document.createElement("div");
		notification.className = `alert alert-${type} alert-dismissible fade show position-fixed top-0 end-0 m-3`;
		notification.style.zIndex = "9999";
		notification.innerHTML = `
            ${message}
            <button type="button" class="btn-close" data-bs-dismiss="alert"></button>
        `;
		document.body.appendChild(notification);

		setTimeout(() => {
			notification.remove();
		}, 3000);
	}

	// Improve error handling
	function handleError(error) {
		console.error("Error:", error);
		showNotification(error.message || "An error occurred. Please try again.", "danger");
	}

	// Add loading state handler
	function setLoading(element, isLoading) {
		if (isLoading) {
			element.classList.add("loading");
		} else {
			element.classList.remove("loading");
		}
	}

	// Update the fetch calls with better error handling
	function toggleStar(queryId) {
		const queryItem = document.querySelector(`[data-id="${queryId}"]`);
		setLoading(queryItem, true);
		fetch("/toggle_star", {
			method: "POST",
			headers: {
				"Content-Type": "application/json",
				"X-CSRFToken": csrfToken,
			},
			body: JSON.stringify({ query_id: queryId }),
		})
			.then((response) => {
				if (!response.ok) throw new Error("Failed to update star status");
				return response.json();
			})
			.then((data) => {
				if (data.success) {
					const icon = queryItem.querySelector(".bi");
					queryItem.classList.toggle("starred");
					icon.classList.toggle("bi-star");
					icon.classList.toggle("bi-star-fill");
					showNotification("Query star status updated");
				} else {
					throw new Error(data.error || "Failed to update star status");
				}
			})
			.catch(handleError)
			.finally(() => setLoading(queryItem, false));
	}
	function toggleArchive(queryId) {
		fetch("/toggle_archive", {
			method: "POST",
			headers: {
				"Content-Type": "application/json",
				"X-CSRFToken": csrfToken,
			},
			body: JSON.stringify({ query_id: queryId }),
		})
			.then((response) => {
				if (!response.ok) throw new Error("Failed to archive query");
				return response.json();
			})
			.then((data) => {
				if (data.success) {
					const queryItem = document.querySelector(`[data-id="${queryId}"]`);
					queryItem.remove();
					showNotification(data.archived ? "Query Archived" : "Query Unarchived");
				} else {
					throw new Error(data.error || "Failed to archive query");
				}
			})
			.catch(handleError);
	}

	// Handle delete functionality
	function deleteQuery(queryId, permanent = false) {
		if (!confirm(permanent ? "Permanently delete this query?" : "Move this query to trash?")) {
			return;
		}

		fetch("/delete_query", {
			method: "POST",
			headers: {
				"Content-Type": "application/json",
				"X-CSRFToken": csrfToken,
			},
			body: JSON.stringify({
				query_id: queryId,
				permanent: permanent,
			}),
		})
			.then((response) => response.json())
			.then((data) => {
				if (data.success) {
					const queryItem = document.querySelector(`[data-id="${queryId}"]`);
					queryItem.remove();
					showNotification("Query Deleted");
				}
			});
	}
	function deleteQueryWOAlert(queryId, permanent = false) {
			fetch("/delete_query", {
			method: "POST",
			headers: {
				"Content-Type": "application/json",
				"X-CSRFToken": csrfToken,
			},
			body: JSON.stringify({
				query_id: queryId,
				permanent: permanent,
			}),
		})
			.then((response) => response.json())
			.then((data) => {
				if (data.success) {
					const queryItem = document.querySelector(`[data-id="${queryId}"]`);
					queryItem.remove();
				}
			});
	}
	function restoreQuery(queryId) {
		if (!confirm("Restore Query")) {
			return;
		}

		fetch("/restore_query", {
			method: "POST",
			headers: {
				"Content-Type": "application/json",
				"X-CSRFToken": csrfToken,
			},
			body: JSON.stringify({
				query_id: queryId,
			}),
		})
			.then((response) => response.json())
			.then((data) => {
				if (data.success) {
					const queryItem = document.querySelector(`[data-id="${queryId}"]`);
					queryItem.remove();
					showNotification("Query Restored");
				}
			});
	}

	// Handle archive functionality
	function archiveQuery(queryId) {
		if (!confirm("Archive this query?")) {
			return;
		}

		fetch("/archive_query", {
			method: "POST",
			headers: {
				"Content-Type": "application/json",
				"X-CSRFToken": csrfToken,
			},
			body: JSON.stringify({ query_id: queryId }),
		})
			.then((response) => response.json())
			.then((data) => {
				if (data.success) {
					const queryItem = document.querySelector(`[data-id="${queryId}"]`);
					const clone = queryItem.cloneNode(true);
					document.getElementById("archiveList").appendChild(clone);
					setupQueryItemListeners(clone);
					queryItem.remove();
					document.querySelector(".empty-archive").style.display = "none";
					updateCounters();
				}
			});
	}

	// Handle bulk actions
	const selectAllCheckbox = document.getElementById("selectAll");
	selectAllCheckbox.addEventListener("change", () => {
		const view = views[currentView];
		view.querySelectorAll(".query-checkbox").forEach((checkbox) => {
			checkbox.checked = selectAllCheckbox.checked;
		});
		updateActionButtons();
	});

	document.getElementById("deleteSelectedBtn").addEventListener("click", () => {
		const view = views[currentView];
		const selected = Array.from(view.querySelectorAll(".query-checkbox:checked"));
		if (selected.length > 0) {
			const permanent = currentView === "trash";
			if (confirm(`${permanent ? "Permanently Delete All Selected Queries" : "Move all slected queries to trash"} ${selected.length} selected queries?`)) {
				selected.forEach((checkbox) => {
					deleteQueryWOAlert(checkbox.value, permanent);
				});
			}
		}
	});

	document.getElementById("archiveSelectedBtn").addEventListener("click", () => {
		const view = views[currentView];
		const selected = Array.from(view.querySelectorAll(".query-checkbox:checked"));
		if (selected.length > 0 && confirm(`Archive ${selected.length} selected queries?`)) {
			selected.forEach((checkbox) => toggleArchive(checkbox.value));
		}
	});

	// Update action buttons state
	function updateActionButtons() {
		const view = views[currentView];
		const hasSelection = view.querySelectorAll(".query-checkbox:checked").length > 0;
		document.getElementById("deleteSelectedBtn").disabled = !hasSelection;
		document.getElementById("archiveSelectedBtn").disabled = !hasSelection || currentView === "archive";
	}

	// Handle refresh button
	document.getElementById("refreshBtn").addEventListener("click", () => {
		location.reload();
	});
});
