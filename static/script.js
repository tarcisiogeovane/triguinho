document.addEventListener("DOMContentLoaded", () => {
    const spinButton = document.getElementById("spinButton");
    const depositPixButton = document.getElementById("depositPixButton");
    const withdrawButton = document.getElementById("withdrawButton");
    const selfExcludeLink = document.getElementById("selfExclude");

    if (spinButton) spinButton.addEventListener("click", spin);
    if (depositPixButton) depositPixButton.addEventListener("click", depositPix);
    if (withdrawButton) withdrawButton.addEventListener("click", withdraw);
    if (selfExcludeLink) selfExcludeLink.addEventListener("click", () => alert("Entre em contato com o suporte para autoexclusão."));
});

function spin() {
    const reels = [
        document.getElementById("reel1"),
        document.getElementById("reel2"),
        document.getElementById("reel3")
    ];
    const spinButton = document.getElementById("spinButton");
    const message = document.getElementById("message");

    if (!reels.every(reel => reel) || !spinButton) {
        console.error("Elementos de rolos ou botão de girar não encontrados.");
        alert("Erro na interface. Recarregue a página.");
        return;
    }

    reels.forEach(reel => reel.classList.add("spinning"));
    spinButton.disabled = true;
    message.textContent = "Girando...";

    fetch("/spin", { method: "POST" })
        .then(response => {
            if (!response.ok) throw new Error("Erro na requisição de giro");
            return response.json();
        })
        .then(data => {
            reels.forEach(reel => reel.classList.remove("spinning"));
            spinButton.disabled = false;

            if (data.error) {
                message.textContent = data.error;
                alert(data.error);
                return;
            }

            document.getElementById("reel1").textContent = data.result[0];
            document.getElementById("reel2").textContent = data.result[1];
            document.getElementById("reel3").textContent = data.result[2];
            document.getElementById("balance").textContent = data.balance.toFixed(2);
            message.textContent = data.message;

            console.log("Giro concluído:", data);
        })
        .catch(error => {
            console.error("Erro no giro:", error);
            reels.forEach(reel => reel.classList.remove("spinning"));
            spinButton.disabled = false;
            message.textContent = "Erro ao girar. Tente novamente.";
            alert("Erro ao girar. Verifique a conexão.");
        });
}

function depositPix() {
    const amount = parseFloat(document.getElementById("depositAmount").value);
    const message = document.getElementById("message");
    const qrCodeDiv = document.getElementById("qrCode");

    if (isNaN(amount) || amount <= 0) {
        message.textContent = "Insira um valor válido.";
        alert("Insira um valor válido.");
        return;
    }

    fetch("/deposit_pix", {
        method: "POST",
        headers: { "Content-Type": "application/x-www-form-urlencoded" },
        body: `amount=${amount}`
    })
        .then(response => {
            if (!response.ok) throw new Error("Erro na requisição de depósito Pix");
            return response.json();
        })
        .then(data => {
            if (data.error) {
                message.textContent = data.error;
                alert(data.error);
                qrCodeDiv.innerHTML = "";
                return;
            }
            qrCodeDiv.innerHTML = `
                <p>Copie o código Pix ou escaneie o QR code:</p>
                <textarea readonly rows="4" style="width: 100%;">${data.qr_code}</textarea>
                <div id="qrcodeCanvas"></div>
            `;
            new QRCode(document.getElementById("qrcodeCanvas"), {
                text: data.qr_code,
                width: 200,
                height: 200
            });
            message.textContent = "Aguardando pagamento Pix...";
            checkPaymentStatus(data.payment_id);
            console.log("Pagamento Pix iniciado:", data);
        })
        .catch(error => {
            console.error("Erro no depósito Pix:", error);
            message.textContent = "Erro ao criar pagamento Pix.";
            alert("Erro ao criar pagamento Pix.");
            qrCodeDiv.innerHTML = "";
        });
}

function checkPaymentStatus(paymentId) {
    const maxAttempts = 60;
    let attempts = 0;
    const message = document.getElementById("message");

    const interval = setInterval(() => {
        if (attempts >= maxAttempts) {
            clearInterval(interval);
            document.getElementById("qrCode").innerHTML = "";
            message.textContent = "Tempo limite para pagamento Pix excedido.";
            alert("Tempo limite para pagamento Pix excedido.");
            return;
        }

        fetch(`/check_payment/${paymentId}`)
            .then(response => {
                if (!response.ok) throw new Error("Erro na verificação de pagamento");
                return response.json();
            })
            .then(data => {
                if (data.status === "approved") {
                    document.getElementById("balance").textContent = data.balance.toFixed(2);
                    message.textContent = data.message;
                    document.getElementById("qrCode").innerHTML = "";
                    document.getElementById("depositAmount").value = "";
                    clearInterval(interval);
                    console.log("Pagamento Pix aprovado:", data);
                } else if (data.status !== "pending") {
                    clearInterval(interval);
                    document.getElementById("qrCode").innerHTML = "";
                    message.textContent = "Pagamento Pix não aprovado.";
                    alert("Pagamento Pix não aprovado.");
                }
            })
            .catch(error => {
                console.error("Erro ao verificar pagamento:", error);
                clearInterval(interval);
                document.getElementById("qrCode").innerHTML = "";
                message.textContent = "Erro ao verificar pagamento Pix.";
                alert("Erro ao verificar pagamento Pix.");
            });

        attempts++;
    }, 5000);
}

function withdraw() {
    const amount = parseFloat(document.getElementById("withdrawAmount").value);
    const message = document.getElementById("message");

    if (isNaN(amount) || amount <= 0) {
        message.textContent = "Insira um valor válido.";
        alert("Insira um valor válido.");
        return;
    }

    fetch("/withdraw", {
        method: "POST",
        headers: { "Content-Type": "application/x-www-form-urlencoded" },
        body: `amount=${amount}`
    })
        .then(response => {
            if (!response.ok) throw new Error("Erro na requisição de saque");
            return response.json();
        })
        .then(data => {
            if (data.error) {
                message.textContent = data.error;
                alert(data.error);
                return;
            }
            document.getElementById("balance").textContent = data.balance.toFixed(2);
            message.textContent = data.message;
            document.getElementById("withdrawAmount").value = "";
            console.log("Saque concluído:", data);
        })
        .catch(error => {
            console.error("Erro no saque:", error);
            message.textContent = "Erro ao sacar. Tente novamente.";
            alert("Erro ao sacar.");
        });
}