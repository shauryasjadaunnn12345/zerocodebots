// Copy embed code
document.getElementById("copyBtn")?.addEventListener("click", () => {
  const code = document.getElementById("embedCode").innerText;
  navigator.clipboard.writeText(code).then(() => {
    const btn = document.getElementById("copyBtn");
    btn.textContent = "✅ Copied!";
    setTimeout(() => (btn.textContent = "📋 Copy"), 2000);
  });
});

// Import from website
(() => {
  const btn = document.getElementById("import-site-btn");
  if (!btn) return;

  btn.addEventListener("click", async () => {
    const url = document.getElementById("website-url").value.trim();
    const result = document.getElementById("import-result");

    if (!url) {
      result.textContent = "Enter a website URL";
      return;
    }

    btn.disabled = true;
    result.textContent = "Importing...";

    try {
      const form = new URLSearchParams();
      form.append("website_url", url);
      form.append("csrfmiddlewaretoken", document.querySelector("[name=csrfmiddlewaretoken]").value);

      if (document.getElementById("use-ai-checkbox")?.checked) {
        form.append("use_ai", "1");
      }

      const res = await fetch(btn.dataset.url, {
        method: "POST",
        headers: { "Content-Type": "application/x-www-form-urlencoded" },
        body: form.toString()
      });

      const data = await res.json();
      result.textContent = res.ok
        ? `Imported ${data.created} items`
        : data.error || "Import failed";

      if (res.ok) setTimeout(() => location.reload(), 900);
    } catch {
      result.textContent = "Import failed";
    } finally {
      btn.disabled = false;
    }
  });
})();
