/* =========================================================
   FIREBASE SERVICE WORKER – BOOK MY APPOINTMENTS
   Single Notification Source (NO DUPLICATES)
   ========================================================= */

importScripts("https://www.gstatic.com/firebasejs/10.7.0/firebase-app-compat.js");
importScripts("https://www.gstatic.com/firebasejs/10.7.0/firebase-messaging-compat.js");

/* ===============================
   FIREBASE INIT
   =============================== */
firebase.initializeApp({
  apiKey: "AIzaSyArBwX8Qd4hZhDDRw1IVRXHMtvRrEab3WE",
  authDomain: "book-my-appointment-41063.firebaseapp.com",
  projectId: "book-my-appointment-41063",
  messagingSenderId: "507072853720",
  appId: "1:507072853720:web:d87e283d449e5f354489ad"
});

const messaging = firebase.messaging();

/* =========================================================
   🔔 BACKGROUND MESSAGE HANDLER (DATA ONLY)
   ========================================================= */
messaging.onBackgroundMessage(function (payload) {
  console.log("📩 Background push received:", payload);

  const title = payload.data?.title || "New Message";

  const options = {
    body: payload.data?.body || "",
    icon: "/static/icons/bma-notification.png",
    badge: "/static/icons/bma-badge.png",
    data: {
      url: payload.data?.url || "/"
    }
  };

  self.registration.showNotification(title, options);
});

/* =========================================================
   👉 NOTIFICATION CLICK → OPEN CHAT / PAGE
   ========================================================= */
self.addEventListener("notificationclick", function (event) {
  event.notification.close();

  const targetUrl = event.notification.data?.url || "/";

  event.waitUntil(
    clients.matchAll({ type: "window", includeUncontrolled: true })
      .then(function (clientList) {
        for (const client of clientList) {
          if (client.url.includes(targetUrl) && "focus" in client) {
            return client.focus();
          }
        }
        if (clients.openWindow) {
          return clients.openWindow(targetUrl);
        }
      })
  );
});
