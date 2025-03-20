const sign_in_btn = document.querySelector("#sign-in-btn");
const sign_up_btn = document.querySelector("#sign-up-btn");
const container = document.querySelector(".container");

sign_up_btn.addEventListener("click", () => {
  container.classList.add("sign-up-mode");
});

sign_in_btn.addEventListener("click", () => {
  container.classList.remove("sign-up-mode");
});


document.addEventListener('DOMContentLoaded', function() {
  
  // Function to handle radio button change
  function handleUserTypeChange() {  
      const userTypeRadio = document.getElementsByName('role');
      const nameInput = document.querySelector('input[name="name"]');
      const rollNumberSection = document.getElementById('roll-number-section');
    if (userTypeRadio[0].checked) { // Student selected
      nameInput.placeholder = 'Name';
      rollNumberSection.classList.remove('hidden'); // Ensure roll number section is visible
    } else if (userTypeRadio[1].checked) { // Librarian selected
      nameInput.placeholder = 'Librarian Name';
      rollNumberSection.classList.add('hidden'); // Hide roll number section
    }
  }
  

  // Event listener for radio button change
  userTypeRadio.forEach(radio => {
    radio.addEventListener('change', handleUserTypeChange);
  });

  // Initial call to set initial state based on default checked radio button
  handleUserTypeChange();

});

document.addEventListener("DOMContentLoaded", function() {
  const alerts = document.querySelectorAll(".alert");
  alerts.forEach(alert => {
    setTimeout(() => {
      alert.style.display = "none";
    }, 5000);
    const closeBtn = alert.querySelector(".close-btn");
    closeBtn.addEventListener("click", () => {
      alert.style.display = "none";
    });
  });
});

document.addEventListener('DOMContentLoaded', function() {
  const userTypeRadio = document.getElementsByName('role');
  const nameInput = document.querySelector('input[name="name"]');
  const rollNumberSection = document.getElementById('roll-number-section');
  const rollNumberInput = document.querySelector('input[name="roll_number"]');

  function handleUserTypeChange() {
    if (userTypeRadio[0].checked) { // Student selected
      nameInput.placeholder = 'Name';
      rollNumberInput.setAttribute('required', ''); // Ensure roll number is required
    } else if (userTypeRadio[1].checked) { // Librarian selected
      nameInput.placeholder = 'Librarian Name';
      rollNumberInput.removeAttribute('required'); // Remove required attribute
    }
  }

  userTypeRadio.forEach(radio => {
    radio.addEventListener('change', handleUserTypeChange);
  });

  handleUserTypeChange(); // Initial setup based on default checked radio
});
