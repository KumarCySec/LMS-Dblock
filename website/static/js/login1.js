const container = document.getElementById('container');
const registerBtn = document.getElementById('register');
const loginBtn = document.getElementById('login');

registerBtn.addEventListener('click', () => {
    container.classList.add("active");
    setTimeout(() => {
        window.location.href = "/signup"; // Change the URL after a short delay
    }, 600); // Adjust the delay to match the duration of your animation (600 milliseconds in this example)
});

loginBtn.addEventListener('click', () => {
    container.classList.remove("active");
    setTimeout(() => {
        window.location.href = "/login"; // Change the URL after a short delay
    }, 600);
});


            document.addEventListener("DOMContentLoaded", function () {
                // Function to handle closing flash messages
                function closeFlashMessage(alertElement) {
                    alertElement.style.display = 'none';
                }
    
                // Auto-hide flash messages after 5 seconds
                setTimeout(function () {
                    var alerts = document.querySelectorAll('.alert');
                    alerts.forEach(function (alert) {
                        closeFlashMessage(alert);
                    });
                }, 5000); // 5000 milliseconds = 5 seconds
    
                // Close button functionality
                var closeButtons = document.querySelectorAll('.close-btn');
                closeButtons.forEach(function (button) {
                    button.addEventListener('click', function () {
                        var alert = this.closest('.alert');
                        closeFlashMessage(alert);
                    });
                });
            });

  