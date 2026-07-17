function fetchPincode(pin) {
  const stateInput = document.getElementById("state");
  const districtInput = document.getElementById("district");
  const postOfficeSelect = document.getElementById("postOffice");

  // reset first
  stateInput.value = "";
  districtInput.value = "";
  postOfficeSelect.innerHTML = `<option value="">Select Post Office</option>`;

  // only when 6 digits
  if (pin.length !== 6 || isNaN(pin)) {
    return;
  }

  fetch(`https://api.postalpincode.in/pincode/${pin}`)
    .then(res => res.json())
    .then(data => {
      if (!data || data[0].Status !== "Success") {
        alert("Invalid Pincode");
        return;
      }

      const offices = data[0].PostOffice;

      // auto fill state & district
      stateInput.value = offices[0].State;
      districtInput.value = offices[0].District;

      // fill post office dropdown
      offices.forEach(po => {
        const opt = document.createElement("option");
        opt.value = po.Name;
        opt.textContent = po.Name;
        postOfficeSelect.appendChild(opt);
      });
    })
    .catch(err => {
      console.error(err);
      alert("Failed to fetch address");
    });
}
