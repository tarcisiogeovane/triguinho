document.getElementById("spinButton").addEventListener("click", spin);
document.getElementById("depositButton").addEventListener("click", deposit);

function spin() {
    fetch("/spin", { method: "POST" })
        .then(response => response.json())
        .then(data => {
            if (data.error) {
                alert(data.error);
                return;
            }
            document.getElementById("reel1").textContent = data.result[0];
            document.getElementById("reel2").textContent = data.result[1];
            document.getElementById("reel3").textContent = data.result[2];
            document.getElementById("balance").textContent = data.balance;
            document.getElementById("message").textContent = data.message;
        });
}

function deposit() {
    const amount = document.getElementById("depositAmount").value;
    fetch("/deposit", {
        method: "POST",
        headers: { "Content-Type": "application/x-www-form-urlencoded" },
        body: `amount=${amount}`
    })
        .then(response => response.json())
        .then(data => {
            if (data.error) {
                alert(data.error);
                return;
            }
            document.getElementById("balance").textContent = data.balance;
            document.getElementById("message").textContent = data.message;
            document.getElementById("depositAmount").value = "";
        });
}