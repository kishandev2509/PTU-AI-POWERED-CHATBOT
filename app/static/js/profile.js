let originalValues = {};
function toggleEdit() {
	const form = document.getElementById("profileForm");
	const inputs = form.querySelectorAll("input, select");
	const actions = form.querySelector(".form-actions");
	isEditing = actions.style.display === "none";
	if (isEditing) {
		inputs.forEach((input) => {
			if (input.hasAttribute("readonly")) return;
			if (input.disabled) {
				originalValues[input.name] = input.value;
				input.disabled = !input.disabled;
			}
		});
         actions.style.display = 'flex';
	} else {
		// 🔹 Restore values if canceling
		inputs.forEach((input) => {
			if (originalValues[input.name] !== undefined) {
				input.value = originalValues[input.name];
				input.disabled = true;
			}
		});
         actions.style.display = 'none';
	}
}

function togglePassword(button) {
	const input = button.parentElement.querySelector("input");
	const icon = button.querySelector("i");

	if (input.type === "password") {
		input.type = "text";
		icon.classList.remove("bi-eye");
		icon.classList.add("bi-eye-slash");
	} else {
		input.type = "password";
		icon.classList.remove("bi-eye-slash");
		icon.classList.add("bi-eye");
	}
}
