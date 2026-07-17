let startY = 0;

document.addEventListener("touchstart", e => {
  startY = e.touches[0].clientY;
});

document.addEventListener("touchend", e => {
  const diff = e.changedTouches[0].clientY - startY;
  if (Math.abs(diff) > 60) {
    const reels = document.querySelector(".reels-container");
    reels.scrollBy({
      top: diff < 0 ? window.innerHeight : -window.innerHeight,
      behavior: "smooth"
    });
  }
});
