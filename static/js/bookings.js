console.log("BOOKINGS JS LOADED");

function loadBookings(date) {
  fetch(`/owner/bookings/date/${date}`)
    .then(res => res.json())
    .then(bookings => {

      let html = `<div class="card"><h3>Bookings for ${date}</h3>`;

      bookings.forEach(b => {
        html += `
          <div class="card booking-card" style="margin-top:16px;">
            <h3>${b.customer_name}</h3>
            <p class="small">${b.email}</p>

            <p class="small">Service: <b>${b.service_name}</b></p>

            <div class="status-row">
              <span class="status ${b.status}">
                ${b.status}
              </span>
            </div>

            ${
              b.status === "pending"
              ? `
                <button class="btn full" onclick="acceptBooking(${b.id})">
                  Accept
                </button>
                <button class="btn danger full"
                        style="margin-top:8px;"
                        onclick="rejectBooking(${b.id})">
                  Reject
                </button>
              `
              : ""
            }
          </div>
        `;
      });

      html += `</div>`;
      document.getElementById("bookingDetails").innerHTML = html;
    });
}

function acceptBooking(id) {
  fetch(`/owner/booking/${id}/accept`, { method: "POST" })
    .then(() => {
      alert("Booking accepted");
      location.reload();
    });
}

function rejectBooking(id) {
  fetch(`/owner/booking/${id}/reject`, { method: "POST" })
    .then(() => {
      alert("Booking rejected");
      location.reload();
    });
}
