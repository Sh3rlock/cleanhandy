let appliedGiftCardAmount = 0;     // deducted value
let giftCardBalance = 0;           // original value
let giftCardActive = false;

let discountCode = null;           // object: { type: "percent"|"fixed", value: number }
let appliedDiscountAmount = 0;     // calculated discount amount

function applyGiftCardOrDiscount(code, callback) {
  if (!code) {
    alert("Please enter a code.");
    return;
  }

  fetch(`/giftcards/api/validate/?code=${encodeURIComponent(code)}`)
    .then(res => res.json())
    .then(data => {
      giftCardActive = false;
      discountCode = null;
      appliedGiftCardAmount = 0;
      appliedDiscountAmount = 0;

      if (!data.valid) {
        alert("❌ Invalid or expired code.");
      } else if (data.type === "giftcard") {
        giftCardActive = true;
        giftCardBalance = parseFloat(data.amount || 0);
        appliedGiftCardAmount = giftCardBalance;
        alert(`✅ Gift Card Applied: -$${appliedGiftCardAmount.toFixed(2)}`);
      } else if (data.type === "discount") {
        discountCode = {
          type: data.discount_type,
          value: parseFloat(data.value)
        };
        alert(`✅ Discount Code Applied: ${discountCode.value}${discountCode.type === 'percent' ? '%' : '$'} off`);
      }

      if (typeof callback === "function") callback();
    })
    .catch(() => {
      alert("❌ Error validating code.");
      if (typeof callback === "function") callback();
    });
}

function updateDiscountUI(amount, label = "Discount") {
  const container = document.getElementById("giftCardApplied");
  const amountEl = document.getElementById("giftCardAmount");

  if (!container || !amountEl) return;

  if (amount > 0) {
    container.style.display = "flex";
    container.querySelector("strong").innerText = `${label}: -$${amount.toFixed(2)}`;
    amountEl.innerText = amount.toFixed(2);
  } else {
    container.style.display = "none";
    amountEl.innerText = "0.00";
  }
}

function calculateDiscount(total) {
  let discount = 0;

  if (giftCardActive && giftCardBalance > 0) {
    discount = Math.min(giftCardBalance, total);
    appliedGiftCardAmount = discount;
    appliedDiscountAmount = 0;
    updateDiscountUI(discount, "Gift Card");
  } else if (discountCode) {
    if (discountCode.type === "fixed") {
      discount = Math.min(discountCode.value, total);
    } else if (discountCode.type === "percent") {
      discount = total * (discountCode.value / 100);
    }
    appliedDiscountAmount = discount;
    appliedGiftCardAmount = 0;
    updateDiscountUI(discount, "Discount");
  } else {
    updateDiscountUI(0);
  }

  return Math.max(total - discount, 0);
}
