const API_BASE = "http://103.50.205.83:8000";

async function loadProducts() {
  try {
    const res = await fetch(`${API_BASE}/products`);
    const data = await res.json();

    const select = document.getElementById("productSelect");
    select.innerHTML = '<option value="">-- Эм сонгох --</option>';

    data.forEach(p => {
      const opt = document.createElement("option");
      opt.value = p.product_url;
      opt.textContent = p.product_url;
      select.appendChild(opt);
    });

    console.log("Products loaded:", data.length);
  } catch (err) {
    console.error("API error:", err);
  }
}

document.addEventListener("DOMContentLoaded", loadProducts);

