document.addEventListener("DOMContentLoaded", () => {
  const timerEl = document.getElementById("timer");

  // 🔒 SAFETY CHECK (MOST IMPORTANT)
  if (!timerEl) {
    console.warn("OTP timer element not found. Skipping otp.js");
    return;
  }

  let time = 120;

  const interval = setInterval(() => {
    timerEl.innerText = time;
    time--;

    if (time < 0) {
      clearInterval(interval);
    }
  }, 1000);
});
