document.addEventListener('DOMContentLoaded', () => {
    const timers = document.querySelectorAll('.timer');

    function updateTimers() {
        timers.forEach(timer => {
            const deadline = new Date(timer.getAttribute('data-deadline'));
            const now = new Date();
            const remainingTime = deadline - now;

            if (remainingTime <= 0) {
                timer.textContent = 'Deadline Passed';
                timer.classList.add('expired');
            } else {
                const days = Math.floor(remainingTime / (1000 * 60 * 60 * 24));
                const hours = Math.floor((remainingTime % (1000 * 60 * 60 * 24)) / (1000 * 60 * 60));
                const minutes = Math.floor((remainingTime % (1000 * 60 * 60)) / (1000 * 60));
                const seconds = Math.floor((remainingTime % (1000 * 60)) / 1000);

                timer.textContent = `${days}d ${hours}h ${minutes}m ${seconds}s`;
            }
        });
    }

    updateTimers();
    setInterval(updateTimers, 1000);
});
