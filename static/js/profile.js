/* =========================================================
   PROFILE TAB HANDLER
   (NO BOOKING LOGIC HERE – VERY IMPORTANT)
   ========================================================= */

function showTab(id) {

  // hide all tab contents
  document.querySelectorAll(".tab-content").forEach(el => {
    el.style.display = "none";
  });

  // show selected tab
  const tab = document.getElementById(id);

  if (!tab) return;

  if (tab.classList.contains("grid-3")) {
    tab.style.display = "grid";
  } else {
    tab.style.display = "block";
  }

  // active tab styling
  document.querySelectorAll(".tab").forEach(t => {
    t.classList.remove("active");
  });

  if (event && event.target) {
    event.target.classList.add("active");
  }

  // 🔥 load booking calendar ONLY when booking tab is opened
  if (id === "booking") {
    loadBookingCalendar();
  }
}

/* =========================================================
   LOAD BOOKING CALENDAR (HTML ONLY)
   ========================================================= */

function loadBookingCalendar() {
  fetch("/owner/bookings")
    .then(res => res.text())
    .then(html => {
      const cal = document.getElementById("bookingCalendar");
      const details = document.getElementById("bookingDetails");

      if (cal) cal.innerHTML = html;
      if (details) details.innerHTML = "";
    })
    .catch(err => {
      console.error("Failed to load booking calendar", err);
    });
}
