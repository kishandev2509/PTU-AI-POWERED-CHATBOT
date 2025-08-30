// Animate stats counter
document.addEventListener("DOMContentLoaded", function () {
	const statNumbers = document.querySelectorAll(".stat-number");

	function animateValue(element, start, end, duration) {
		let startTimestamp = null;
		const step = (timestamp) => {
			if (!startTimestamp) startTimestamp = timestamp;
			const progress = Math.min((timestamp - startTimestamp) / duration, 1);
			const value = Math.floor(progress * (end - start) + start);
			element.textContent = value.toLocaleString();
			if (progress < 1) {
				window.requestAnimationFrame(step);
			}
		};
		window.requestAnimationFrame(step);
	}

	// Intersection Observer to trigger animation when element is in view
	const observer = new IntersectionObserver(
		(entries) => {
			entries.forEach((entry) => {
				if (entry.isIntersecting) {
					const target = entry.target;
					const endValue = parseInt(target.getAttribute("data-count"));
					animateValue(target, 0, endValue, 2000);
					observer.unobserve(target);
				}
			});
		},
		{ threshold: 0.5 }
	);

	statNumbers.forEach((stat) => {
		observer.observe(stat);
	});
});

// Add this to your existing script section or create a new one
document.addEventListener("DOMContentLoaded", function () {
	// Initialize the carousel with a 5-second interval and smooth transitions
	new bootstrap.Carousel(document.querySelector("#ptuCarousel"), {
		interval: 5000,
		ride: "carousel",
		wrap: true,
		touch: true,
	});

	// Add smooth transition class to carousel
	document.querySelector("#ptuCarousel").classList.add("slide");
});

function openChatbot() {
	document.getElementById("chatbotModal").style.display = "block";
}

function closeChatbot() {
	document.getElementById("chatbotModal").style.display = "none";
}

function redirectToLogin() {
	window.location.href = "{{ url_for('auth.login') }}";
}

function sendMessage() {
	const input = document.getElementById("userInput");
	const message = input.value.trim();
	const csrfToken = document.querySelector('meta[name="csrf-token"]').getAttribute("content");

	if (message) {
		addMessage("user", message);
		userInput.value = "";
		// Show typing indicator
		const typingIndicator = document.getElementById("typing-indicator");
		if (typingIndicator) {
			typingIndicator.classList.add("active");
		}

		// Send message to server
		fetch("/chat", {
			method: "POST",
			headers: {
				"Content-Type": "application/json",
				"X-CSRFToken": csrfToken,
			},
			body: JSON.stringify({ message: message }),
		})
			.then((response) => response.json())
			.then((data) => {
				// Hide typing indicator
				if (typingIndicator) {
					typingIndicator.classList.remove("active");
				}

				// Add bot response to chat
				if (data.response) {
					addMessage("bot", data.response);
				}
			})
			.catch((error) => {
				console.error("Error:", error);
				if (typingIndicator) {
					typingIndicator.classList.remove("active");
				}
				addMessage("bot", "Sorry, there was an error processing your message.");
			});
	}
}

function handleKeyPress(event) {
	if (event.key === "Enter") {
		sendMessage();
	}
}

function addMessage(type, text) {
	const messagesDiv = document.getElementById("chatMessages");
	const messageDiv = document.createElement("div");
	messageDiv.className = `message ${type}-message`;

	const content = document.createElement("div");
	content.className = "message-content";

	if (type === "bot") {
		const icon = document.createElement("i");
		icon.className = "bi bi-robot";
		content.appendChild(icon);
	}

	const textDiv = document.createElement("div");
	textDiv.className = "message-text";
	textDiv.textContent = text;
	content.appendChild(textDiv);

	messageDiv.appendChild(content);
	messagesDiv.appendChild(messageDiv);
	messagesDiv.scrollTop = messagesDiv.scrollHeight;
}

// Close chatbot when clicking outside
window.onclick = function (event) {
	const modal = document.getElementById("chatbotModal");
	if (event.target === modal) {
		closeChatbot();
	}
};
