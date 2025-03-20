document.addEventListener("DOMContentLoaded", function () {
    const sidebarToggle = document.querySelector("#sidebar-toggle");
    const sidebar = document.querySelector("#sidebar");
    const themeToggle = document.getElementById('themeToggle');

    // Ensure elements exist before adding event listeners
    if (sidebarToggle && sidebar) {
        sidebarToggle.addEventListener("click", function() {
            sidebar.classList.toggle("collapsed");
        });
    }

    if (themeToggle) {
        // Initialize the theme based on localStorage
        const savedTheme = localStorage.getItem('theme');
        const isDark = savedTheme === 'dark';

        document.documentElement.setAttribute('data-bs-theme', isDark ? 'dark' : 'light');
        themeToggle.checked = isDark;

        // Toggle theme on switch change
        themeToggle.addEventListener('change', function () {
            toggleTheme();
        });
    }
});

function toggleTheme() {
    const currentTheme = document.documentElement.getAttribute('data-bs-theme');
    const newTheme = currentTheme === 'dark' ? 'light' : 'dark';

    document.documentElement.setAttribute('data-bs-theme', newTheme);
    localStorage.setItem('theme', newTheme);
}

document.querySelector(".theme-toggle").addEventListener("click",() => {
    toggleLocalStorage();
    toggleRootClass();
});

function toggleRootClass(){
    const current = document.documentElement.getAttribute('data-bs-theme');
    const inverted = current == 'dark' ? 'light' : 'dark';
    document.documentElement.setAttribute('data-bs-theme',inverted);
}

function toggleLocalStorage(){
    if(isLight()){
        localStorage.removeItem("light");
    }else{
        localStorage.setItem("light","set");
    }
}

function isLight(){
    return localStorage.getItem("light");
}

if(isLight()){
    toggleRootClass();
}

