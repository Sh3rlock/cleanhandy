let appliedGiftCardAmount = 0;  // actual value to deduct
let giftCardBalance = 0;          // full value from API
let giftCardActive = false;

function applyGiftCard(code, callback) {
  if (!code) {
    alert("Please enter a gift card code.");
    return;
  }

  fetch(`/giftcards/api/validate/?code=${encodeURIComponent(code)}`)
    .then(res => res.json())
    .then(data => {
      if (data.valid) {
        appliedGiftCardAmount = parseFloat(data.amount || 0);
        giftCardBalance = parseFloat(data.amount || 0);
        appliedGiftCardAmount = giftCardBalance;
        giftCardActive = true;
        alert(`✅ Gift Card Applied: -$${appliedGiftCardAmount.toFixed(2)}`);
      } else {
        alert("❌ Invalid or expired gift card.");
        appliedGiftCardAmount = 0;
      }

      if (typeof callback === "function") callback(appliedGiftCardAmount);
    })
    .catch(() => {
      alert("❌ Error validating gift card.");
      if (typeof callback === "function") callback(0);
    });
}

function updateGiftCardUI(amount) {
  const giftEl = document.getElementById("giftCardApplied");
  const giftAmtEl = document.getElementById("giftCardAmount");

  if (!giftEl || !giftAmtEl) return;

  if (amount > 0) {
    giftEl.style.display = "flex";
    giftAmtEl.innerText = amount.toFixed(2);
  } else {
    giftEl.style.display = "none";
    giftAmtEl.innerText = "0.00";
  }
}
