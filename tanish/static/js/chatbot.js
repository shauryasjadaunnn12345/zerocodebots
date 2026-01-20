(() => {
  const cfg = window.CHATBOT_CONFIG;
  const box = document.getElementById("chat-box");
  const form = document.getElementById("chat-form");
  const input = document.getElementById("chat-input");

  if (!form || !box || !input) return;

  function bubble(text, cls) {
    const d = document.createElement("div");
    d.className = `chat-bubble ${cls}`;
    d.textContent = text;
    box.appendChild(d);
    box.scrollTop = box.scrollHeight;
    return d;
  }

  function typingBubble() {
    const d = document.createElement("div");
    d.className = "chat-bubble bot typing";
    d.innerHTML = "<span></span><span></span><span></span>";
    box.appendChild(d);
    box.scrollTop = box.scrollHeight;
    return d;
  }

  async function askBot(question) {
    const res = await fetch(cfg.askUrl, {
      method: "POST",
      headers: {
        "X-CSRFToken": cfg.csrf,
        "Content-Type": "application/x-www-form-urlencoded"
      },
      body: new URLSearchParams({ question })
    });

    if (!res.ok) throw new Error("Bad response");
    return res.json();
  }

  form.addEventListener("submit", async e => {
    e.preventDefault();

    const q = input.value.trim();
    if (!q) return;

    bubble(q, "user");
    input.value = "";

    // show typing loader immediately
    const loader = typingBubble();

    try {
      const data = await askBot(q);
      loader.remove();
      bubble(data.answer || "No answer found.", "bot");
    } catch (err) {
      loader.remove();
      bubble("⚠️ Server error. Please try again.", "bot");
    }
  });

  /* Lazy-load Speech Recognition only on click */
  const micBtn = document.getElementById("mic-button");
  if (cfg.voiceEnabled && micBtn) {
    micBtn.addEventListener("click", () => {
      const SR = window.SpeechRecognition || window.webkitSpeechRecognition;
      if (!SR) return;

      const rec = new SR();
      rec.lang = cfg.lang === "hi" ? "hi-IN" : "en-IN";

      micBtn.classList.add("active");
      rec.start();

      rec.onresult = e => {
        input.value = e.results[0][0].transcript;
        form.requestSubmit();
      };

      rec.onend = () => micBtn.classList.remove("active");
      rec.onerror = () => micBtn.classList.remove("active");
    });
  }
})();
