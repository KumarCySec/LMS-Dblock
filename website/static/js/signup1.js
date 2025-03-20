// Define a function to generate years
function generateYears() {
    // Get the select element
    var selectElement = document.getElementById("year_of_graduation");
  
    // Get the current year
    var currentYear = new Date().getFullYear();
  
    // Add options for years from current year to 1970
    for (var year = currentYear+5; year >= 1970; year--) {
      var option = document.createElement("option");
      option.text = year;
      option.value = year;
      selectElement.appendChild(option);
    }
  }
  
  // Call the function after the DOM content is fully loaded
  document.addEventListener("DOMContentLoaded", function() {
    generateYears();
  });
  