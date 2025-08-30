document.querySelectorAll(".profile-photo-upload").forEach((input) => {
    input.addEventListener("change", function (e) {
	const csrfToken = document.querySelector('meta[name="csrf-token"]').getAttribute("content");
	const file = e.target.files[0];
	if (file) {
		const formData = new FormData();
		formData.append("photo", file);

		// Show loading state
		const photoElement = input.closest(".profile-photo-container").querySelector(".profile-photo");
		photoElement.style.opacity = "0.5";

		fetch("/upload_profile_photo", {
			method: "POST",
			headers: {
				"X-CSRFToken": csrfToken, // ✅ Send CSRF token
			},
			body: formData,
		})
			.then(async (response) => {
				const contentType = response.headers.get("content-type");

				if (contentType && contentType.includes("application/json")) {
					// ✅ Safe to parse as JSON
					return response.json();
				} else {
					// ⚠️ Not JSON, log raw text (likely an error page)
					const text = await response.text();
					console.error("Server returned non-JSON:", text);
					throw new Error("Server did not return JSON");
				}
			})
			.then((data) => {
				if (data.success) {
					// Update the profile photo with the new one
					photoElement.src = data.photo_url;
					photoElement.style.opacity = "1";
				} else {
					alert("Failed to update profile photo: " + (data.error || "Unknown error"));
					photoElement.style.opacity = "1";
				}
			})
			.catch((error) => {
				console.error("Error:", error);
				alert("An error occurred while updating the profile photo.");
				photoElement.style.opacity = "1";
			});
	}
});
});
// Navbar scroll effect
window.addEventListener("scroll", function () {
	const navbar = document.querySelector(".navbar");
	if (window.scrollY > 50) {
		navbar.classList.add("scrolled");
	} else {
		navbar.classList.remove("scrolled");
	}
});

document.addEventListener("DOMContentLoaded", function () {
	// Get current page URL path
	const currentPath = window.location.pathname;

	// Get all nav links
	const navLinks = document.querySelectorAll(".nav-link");

	// Loop through nav links and add active class if href matches current path
	navLinks.forEach((link) => {
		if (link.getAttribute("href") === currentPath) {
			link.classList.add("active");
		}

		// Add click handler to update active state
		link.addEventListener("click", function () {
			navLinks.forEach((l) => l.classList.remove("active"));
			this.classList.add("active");
		});
	});
});
function showMoreNotices() {
    const hiddenNotices = document.querySelectorAll(".hidden-notice");
    const showMoreBtn = document.querySelector(".show-more-btn");

    hiddenNotices.forEach((notice) => {
        notice.style.display = "flex";
        notice.classList.remove("hidden-notice");
    });

    if (showMoreBtn) {
        showMoreBtn.style.display = "none";
    }
}