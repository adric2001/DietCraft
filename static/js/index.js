document.addEventListener("DOMContentLoaded", function() {
    setTimeout(function() {
        const flashMessages = document.querySelectorAll(".flash");
        flashMessages.forEach(message => {
            message.style.display = "none";
        });
    }, 2000);
});