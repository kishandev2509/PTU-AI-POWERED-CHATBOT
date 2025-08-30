document.addEventListener("DOMContentLoaded", function () {
	// Voice Input Setup
	const voiceBtn = document.getElementById("voice-btn");
	const userInput = document.getElementById("user-input");
	const sendBtn = document.getElementById("send-btn");
	let recognition = null;

	if ("webkitSpeechRecognition" in window) {
		recognition = new webkitSpeechRecognition();
		recognition.continuous = false;
		recognition.interimResults = false;
		recognition.lang = "en-US";

		recognition.onstart = function () {
			voiceBtn.classList.add("active");
		};

		recognition.onend = function () {
			voiceBtn.classList.remove("active");
		};

		recognition.onresult = function (event) {
			const transcript = event.results[0][0].transcript;
			userInput.value = transcript;
			sendMessage();
		};

		recognition.onerror = function (event) {
			console.error("Speech recognition error:", event.error);
			voiceBtn.classList.remove("active");
		};

		voiceBtn.addEventListener("click", function () {
			if (recognition) {
				try {
					recognition.start();
				} catch (error) {
					console.error("Error starting speech recognition:", error);
				}
			}
		});
	} else {
		voiceBtn.style.display = "none";
	}

	// Send Message Function
	window.sendMessage = function () {
		const message = userInput.value.trim();

		if (message) {
			// Add user message to chat
			const csrfToken = document.querySelector('meta[name="csrf-token"]').getAttribute("content");
			addMessageToChat(message, "user");
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
					addMessageToChat(data.response, "bot");
				})
				.catch((error) => {
					console.error("Error:", error);
					if (typingIndicator) {
						typingIndicator.classList.remove("active");
					}
					addMessageToChat("Sorry, there was an error processing your message.", "bot");
				});
		}
	};

	// Event Listeners for sending messages
	sendBtn.addEventListener("click", sendMessage);

	userInput.addEventListener("keypress", function (e) {
		if (e.key === "Enter") {
			sendMessage();
		}
	});

	// Function to add messages to chat
	function addMessageToChat(message, sender) {
		const chatMessages = document.getElementById("chat-messages");
		if (!chatMessages) return;

		const messageDiv = document.createElement("div");
		messageDiv.className = `message ${sender}-message`;

		const contentDiv = document.createElement("div");
		contentDiv.className = "message-content";

		const textDiv = document.createElement("div");
		textDiv.className = "message-text";
		textDiv.innerHTML = message;

		const timeDiv = document.createElement("div");
		timeDiv.className = "message-time";
		timeDiv.textContent = new Date().toLocaleTimeString();

		contentDiv.appendChild(textDiv);
		messageDiv.appendChild(contentDiv);
		messageDiv.appendChild(timeDiv);

		chatMessages.appendChild(messageDiv);
		requestAnimationFrame(() => {
			chatContainer = document.getElementById("chat-container");
			chatContainer.scrollTo({
				top: chatContainer.scrollHeight,
				behavior: "smooth",
			});
		});
	}

	// Quick Links functionality
	const quickLinksBtn = document.getElementById("quick-links-toggle");
	const quickLinksSidebar = document.getElementById("quick-links-sidebar");
	const closeSidebarBtn = document.getElementById("close-sidebar");
	const quickQueryLinks = document.querySelectorAll(".quick-query");

	// Toggle Quick Links sidebar
	if (quickLinksBtn && quickLinksSidebar) {
		quickLinksBtn.addEventListener("click", function () {
			quickLinksSidebar.classList.add("active");
		});
	}

	// Close Quick Links sidebar
	if (closeSidebarBtn && quickLinksSidebar) {
		closeSidebarBtn.addEventListener("click", function () {
			quickLinksSidebar.classList.remove("active");
		});
	}

	// Handle Quick Query clicks
	quickQueryLinks.forEach((link) => {
		link.addEventListener("click", function (e) {
			e.preventDefault();
			const query = this.getAttribute("data-query");
			const userInput = document.getElementById("user-input");

			if (userInput && query) {
				userInput.value = query;
				quickLinksSidebar.classList.remove("active");
				sendMessage();
			}
		});
	});

	// Close sidebar when clicking outside
	document.addEventListener("click", function (e) {
		if (quickLinksSidebar && quickLinksSidebar.classList.contains("active")) {
			if (!quickLinksSidebar.contains(e.target) && e.target !== quickLinksBtn) {
				quickLinksSidebar.classList.remove("active");
			}
		}
	});

	// New Chat Button
	const newChatBtn = document.getElementById("new-chat-btn");
	if (newChatBtn) {
		newChatBtn.addEventListener("click", function () {
			const chatMessages = document.getElementById("chat-messages");
			if (chatMessages) {
				chatMessages.innerHTML = "";
			}

			// Don't clear the history, just show success
			alert("New chat started! Your chat history is still available.");
		});
	}

	// History Toggle
	const historyToggleBtn = document.getElementById("history-toggle-btn");
	const historyCloseBtn = document.getElementById("history-close-btn");
	const chatHistorySidebar = document.getElementById("chat-history-sidebar");

	if (historyToggleBtn && chatHistorySidebar) {
		historyToggleBtn.addEventListener("click", function () {
			chatHistorySidebar.classList.add("active");
			loadChatHistory(); // Load history when sidebar is opened
		});
	}

	if (historyCloseBtn && chatHistorySidebar) {
		historyCloseBtn.addEventListener("click", function () {
			chatHistorySidebar.classList.remove("active");
		});
	}

	// Live Support
	const liveSupportBtn = document.getElementById("live-support");
	const liveSupportModal = document.getElementById("live-support-modal");
	const closeModalBtn = document.getElementById("close-modal");
	const supportForm = document.getElementById("support-form");

	if (liveSupportBtn && liveSupportModal) {
		liveSupportBtn.addEventListener("click", function () {
			liveSupportModal.classList.add("active");
		});
	}

	if (closeModalBtn && liveSupportModal) {
		closeModalBtn.addEventListener("click", function () {
			liveSupportModal.classList.remove("active");
		});
	}

	// Live support form submission
	document.getElementById("support-form").addEventListener("submit", function (e) {
		e.preventDefault();

		const formData = {
			name: document.getElementById("name").value,
			email: document.getElementById("email").value,
			query: document.getElementById("query").value,
		};
		const csrfToken = document.querySelector('meta[name="csrf-token"]').getAttribute("content");

		fetch(send_support_email_url, {
			method: "POST",
			headers: {
				"Content-Type": "application/json",
				"X-CSRFToken": csrfToken,
			},
			body: JSON.stringify(formData),
		})
			.then((response) => response.json())
			.then((data) => {
				if (data.success) {
					alert("Your message has been sent successfully! We will contact you soon.");
					document.getElementById("live-support-modal").style.display = "none";
					document.getElementById("support-form").reset();
				} else {
					alert(data.message || "Failed to send message. Please try again.");
				}
			})
			.catch((error) => {
				console.error("Error:", error);
				alert("An error occurred. Please try again.");
			});
	});

	// Chat History functionality
	function loadChatHistory() {
		fetch("/get_chat_history")
			.then((response) => response.json())
			.then((data) => {
				const chatMessages = document.getElementById("chat-messages");
				const historyList = document.getElementById("chat-history-list");

				// Clear existing history
				historyList.innerHTML = "";
				console.log(data)

				// Group chats by date
				const chatsByDate = {};
				data.history.forEach((chat) => {
					const date = chat.created_at.split(" ")[0];
					if (!chatsByDate[date]) {
						chatsByDate[date] = [];
					}
					chatsByDate[date].push(chat);
				});

				// Add chats to history sidebar
				Object.keys(chatsByDate)
					.forEach((date) => {
						const dateHeader = document.createElement("div");
						dateHeader.className = "history-date-header";
						dateHeader.textContent = formatDate(date);
						historyList.appendChild(dateHeader);

						chatsByDate[date].reverse().forEach((chat) => {
							const historyItem = document.createElement("div");
							historyItem.className = "chat-history-item";
							historyItem.innerHTML = `
                        <div class="history-time">${chat.user_timestamp.split(" ")[1]}</div>
                        <div class="history-message">${chat.user_message}</div>
                    `;
							historyList.appendChild(historyItem);

							// Add click event to show the full conversation
							historyItem.addEventListener("click", () => {
								chatMessages.innerHTML = "";
								addMessageToChat(chat.user_message, "user");
								addMessageToChat(chat.bot_response, "bot");
							});
						});
					});
			})
			.catch((error) => console.error("Error loading chat history:", error));
	}

	function formatDate(dateStr) {
		const date = new Date(dateStr);
		const today = new Date();
		const yesterday = new Date(today);
		yesterday.setDate(yesterday.getDate() - 1);

		if (dateStr === today.toISOString().split("T")[0]) {
			return "Today";
		} else if (dateStr === yesterday.toISOString().split("T")[0]) {
			return "Yesterday";
		}
		return date.toLocaleDateString();
	}
});
