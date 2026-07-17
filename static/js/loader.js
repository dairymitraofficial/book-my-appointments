function showLoader(text = "Processing...") {
  const loader = document.getElementById("globalLoader");
  loader.querySelector("p").innerText = text;
  loader.classList.remove("hidden");
}

function hideLoader() {
  document.getElementById("globalLoader").classList.add("hidden");
}
