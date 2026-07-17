/* ==================================================
   FEED.JS — FULL & FIXED
================================================== */

/* ===============================
   LIKE / UNLIKE
================================= */
function toggleLike(btn) {
  if (!btn) return;

  const serviceId = btn.dataset.id;
  const liked = btn.dataset.liked === "1";

  const url = liked
    ? `/customer/post/${serviceId}/unlike`
    : `/customer/post/${serviceId}/like`;

  fetch(url, {
    method: "POST",
    credentials: "same-origin"
  })
    .then(res => res.json())
    .then(data => {
      btn.dataset.liked = liked ? "0" : "1";

      const heart = btn.querySelector(".heart");
      if (heart) heart.innerText = liked ? "🤍" : "❤️";

      const countEl = document.getElementById(`likes-${serviceId}`);
      if (countEl) countEl.innerText = data.likes;
    })
    .catch(err => {
      console.error("LIKE ERROR:", err);
      alert("Like failed");
    });
}

/* ===============================
   DOUBLE TAP LIKE + ANIMATION
================================= */
function doubleTapLike(container, serviceId) {
  if (!container) return;

  const bigHeart = container.querySelector(".big-heart");
  if (bigHeart) {
    bigHeart.classList.add("show");
    setTimeout(() => bigHeart.classList.remove("show"), 800);
  }

  const btn = document.querySelector(
    `.like-btn[data-id="${serviceId}"]`
  );

  if (btn && btn.dataset.liked === "0") {
    toggleLike(btn);
  }
}

/* ===============================
   INFINITE SCROLL (IMPORTANT FIX)
================================= */

let feedOffset = 30;
let feedLoading = false;
let feedEnded = false;

document.addEventListener("DOMContentLoaded", () => {
  const reelsContainer = document.querySelector(".reels-container");
  if (!reelsContainer) return;

  reelsContainer.addEventListener("scroll", () => {
    if (feedLoading || feedEnded) return;

    const nearBottom =
      reelsContainer.scrollTop +
      reelsContainer.clientHeight >=
      reelsContainer.scrollHeight - 300;

    if (nearBottom) {
      loadMoreReels();
    }
  });
});

function loadMoreReels() {
  feedLoading = true;

  fetch(`/customer/feed/load?offset=${feedOffset}`, {
    credentials: "same-origin"
  })
    .then(res => res.json())
    .then(posts => {
      if (!posts || posts.length === 0) {
        feedEnded = true;
        return;
      }

      const container = document.querySelector(".reels-container");

      posts.forEach(p => {
        container.insertAdjacentHTML("beforeend", buildReelHTML(p));
      });

      feedOffset += posts.length;
    })
    .catch(err => {
      console.error("INFINITE LOAD ERROR:", err);
    })
    .finally(() => {
      feedLoading = false;
    });
}

/* ===============================
   BUILD HTML FOR NEW REELS
================================= */
function buildReelHTML(p) {
  const liked = p.liked ? "1" : "0";
  const heart = p.liked ? "❤️" : "🤍";
  const photo = p.profile_photo || "default.png";

  return `
  <div class="reel">
    <div class="reel-media"
         ondblclick="doubleTapLike(this, ${p.service_id})">
      <img src="/static/${p.image}" class="reel-image">
      <div class="big-heart">❤️</div>
    </div>

    <div class="reel-overlay">

      <div class="reel-top">
        <a href="/customer/owner/${p.owner_id}">
          <img src="/static/uploads/owner_profiles/${photo}"
               class="reel-avatar">
          <span>${p.business_name}</span>
        </a>
      </div>

      <div class="reel-actions">
        <button class="like-btn"
          data-id="${p.service_id}"
          data-liked="${liked}"
          onclick="toggleLike(this)">
          <span class="heart">${heart}</span>
          <small id="likes-${p.service_id}">
            ${p.like_count}
          </small>
        </button>
      </div>

      <div class="reel-bottom">
        <b>${p.service_name}</b>
        <div class="price">₹${p.price}</div>
      </div>

    </div>
  </div>
  `;
}

/* ===============================
   PREVENT DOUBLE TAP ZOOM
================================= */
document.addEventListener("dblclick", e => {
  e.preventDefault();
}, { passive: false });
