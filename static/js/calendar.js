function selectDate(date) {
  document.getElementById("selectedDate").value = date;
  document.getElementById("confirmBtn").disabled = false;

  document.querySelectorAll(".date").forEach(d => {
    d.classList.remove("selected");
  });

  event.target.classList.add("selected");
}
