let index = 0;

document.addEventListener("DOMContentLoaded", () => {
  window.imgs = document.querySelectorAll("#carousel img");
  window.counter = document.getElementById("counter");

  if (!imgs || imgs.length === 0) return;

  showImg(index);

  // 👉 Mobile swipe support
  let startX = 0;
  const carousel = document.getElementById("carousel");

  carousel.addEventListener("touchstart", e => {
    startX = e.touches[0].clientX;
  });

  carousel.addEventListener("touchend", e => {
    const diff = e.changedTouches[0].clientX - startX;
    if (Math.abs(diff) > 40) {
      diff < 0 ? nextImg() : prevImg();
    }
  });
});

function showImg(i) {
  imgs.forEach(img => img.classList.remove("active"));
  imgs[i].classList.add("active");

  if (counter) {
    counter.innerText = `${i + 1} / ${imgs.length}`;
  }
}

function nextImg() {
  index = (index + 1) % imgs.length;
  showImg(index);
}

function prevImg() {
  index = (index - 1 + imgs.length) % imgs.length;
  showImg(index);
}
