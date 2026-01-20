document.addEventListener("DOMContentLoaded", () => {
  const form = document.querySelector(".create-project-form");
  const submitBtn = document.querySelector(".create-project-submit");

  if (form) {
    form.addEventListener("submit", () => {
      submitBtn.disabled = true;
      submitBtn.textContent = "Creating...";
    });
  }
});
