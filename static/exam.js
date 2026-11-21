
(() => {
  "use strict";

  const cfg = window.NEET_CONFIG;
  if (!cfg) return;

  const timer = document.getElementById("timer");
  const status = document.getElementById("save-status");
  const form = document.getElementById("submit-form");

  const deadline = Date.parse(cfg.deadline);
  let submitted = false;
  let pending = 0;

  function showStatus(message) {
    if (status) status.textContent = message;
  }

  function updateAnswered() {
    const answered = new Set(
      [...document.querySelectorAll('input[type="radio"]:checked')]
        .map(input => input.dataset.q)
    ).size;

    const counter = document.getElementById("answered");
    if (counter) counter.textContent = answered;
  }

  function updateTimer() {
    if (!timer || !Number.isFinite(deadline)) return;

    const remaining = Math.max(
      0,
      Math.ceil((deadline - Date.now()) / 1000)
    );

    const hours = String(Math.floor(remaining / 3600)).padStart(2, "0");
    const minutes = String(
      Math.floor((remaining % 3600) / 60)
    ).padStart(2, "0");
    const seconds = String(remaining % 60).padStart(2, "0");

    timer.textContent = `${hours}:${minutes}:${seconds}`;

    if (remaining === 0 && !submitted && form) {
      submitted = true;
      showStatus("Time is up. Submitting answer sheet...");
      form.submit();
    }
  }

  async function saveAnswer(question, option) {
    pending++;
    showStatus("Saving answer...");

    try {
      const response = await fetch(cfg.saveUrl, {
        method: "POST",
        headers: {
          "Content-Type": "application/json"
        },
        credentials: "same-origin",
        body: JSON.stringify({
          q: Number(question),
          option: option
        })
      });

      if (!response.ok) throw new Error("Save failed");

      showStatus("Answers saved");
    } catch (error) {
      showStatus("Save failed. Check your connection and retry.");
    } finally {
      pending--;
    }
  }

  document.querySelectorAll(".tab").forEach(tab => {
    tab.addEventListener("click", () => {
      document.querySelectorAll(".tab").forEach(item => {
        item.classList.toggle("active", item === tab);
      });

      document.querySelectorAll(".subject").forEach(section => {
        section.classList.toggle(
          "hidden",
          section.dataset.section !== tab.dataset.tab
        );
      });
    });
  });

  document.querySelectorAll('input[type="radio"][data-q]')
    .forEach(input => {
      input.addEventListener("change", () => {
        updateAnswered();
        saveAnswer(input.dataset.q, input.value);
      });
    });

  document.querySelectorAll("button[data-clear]")
    .forEach(button => {
      button.addEventListener("click", () => {
        const question = button.dataset.clear;

        document.querySelectorAll(
          'input[type="radio"][data-q="' + question + '"]'
        ).forEach(input => {
          input.checked = false;
        });

        updateAnswered();
        saveAnswer(question, null);
      });
    });

  if (form) {
    form.addEventListener("submit", event => {
      if (submitted) return;

      if (pending > 0) {
        event.preventDefault();
        alert("Please wait until answers finish saving.");
        return;
      }

      if (!confirm("Submit your final answer sheet?")) {
        event.preventDefault();
      } else {
        submitted = true;
      }
    });
  }

  updateAnswered();
  updateTimer();
  setInterval(updateTimer, 1000);
})();
