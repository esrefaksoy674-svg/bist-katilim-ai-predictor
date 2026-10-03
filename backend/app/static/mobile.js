(() => {
  const root = document.querySelector("main");
  const results = document.querySelector("#results");
  const toolbar = document.querySelector(".toolbar");
  if (!root || !results || !toolbar) return;

  const style = document.createElement("style");
  style.textContent = "@media(max-width:650px){table{min-width:0}thead{display:none}tbody tr{display:grid;grid-template-columns:1fr 1fr;padding:8px 10px;border-bottom:1px solid #223149}td{display:flex;flex-direction:column;gap:3px;padding:8px;border:0;font-size:14px}td::before{content:attr(data-label);color:#9aacc4;font-size:10px;text-transform:uppercase;letter-spacing:.05em}}";
  document.head.append(style);

  const installButton = document.createElement("button");
  installButton.type = "button";
  installButton.textContent = "Uygulamayı yükle";
  installButton.hidden = true;
  toolbar.append(installButton);

  const tracking = document.createElement("section");
  tracking.innerHTML = '<h2 style="font-size:20px;margin:28px 0 4px">Sonuç takibi</h2><p id="tracking-summary" style="margin:0 0 12px;color:#9aacc4;font-size:13px">Gerçekleşen sonuçlar yükleniyor…</p><div id="tracking-history" class="table-wrap"></div>';
  results.after(tracking);
  const summary = tracking.querySelector("#tracking-summary");
  const history = tracking.querySelector("#tracking-history");

  let installPrompt = null;
  window.addEventListener("beforeinstallprompt", (event) => {
    event.preventDefault();
    installPrompt = event;
    installButton.hidden = false;
  });
  installButton.addEventListener("click", async () => {
    if (!installPrompt) return;
    installPrompt.prompt();
    await installPrompt.userChoice;
    installPrompt = null;
    installButton.hidden = true;
  });

  function labelCurrentTable() {
    const labels = ["Hisse", "Hedef tarih", "%5 ve üzeri olasılık", "Beklenen getiri", "Doğrulama başarısı", "Durum"];
    document.querySelectorAll("#results tbody tr").forEach((row) => {
      [...row.children].forEach((cell, index) => { cell.dataset.label = labels[index] || ""; });
    });
  }
  new MutationObserver(labelCurrentTable).observe(results, {childList:true,subtree:true});
  labelCurrentTable();

  const formatPercent = (value) => value == null ? "—" : Number(value).toLocaleString("tr-TR", {maximumFractionDigits:2}) + "%";
  async function loadTracking() {
    try {
      const response = await fetch("/performance?limit=30", {headers:{Accept:"application/json"}});
      if (!response.ok) throw new Error("Unavailable");
      const data = await response.json();
      const rate = data.hit_rate_percent == null ? "—" : Number(data.hit_rate_percent).toLocaleString("tr-TR", {maximumFractionDigits:1}) + "%";
      summary.textContent = "Gerçekleşen +%5 isabet oranı: " + rate + " · " + (data.successful_count || 0) + " başarılı / " + (data.evaluated_count || 0) + " sonuçlandı" + (data.pending_count ? " · " + data.pending_count + " tahmin bekliyor" : "");
      history.replaceChildren();
      const rows = Array.isArray(data.predictions) ? data.predictions : [];
      if (!rows.length) {
        history.textContent = "Tahmin sonuçları oluştukça burada görünecek.";
        history.className = "empty";
        return;
      }
      history.className = "table-wrap";
      const table = document.createElement("table");
      table.innerHTML = "<thead><tr><th>Hisse</th><th>Tahmin günü</th><th>Hedef günü</th><th>Olasılık</th><th>Gerçek getiri</th><th>Sonuç</th></tr></thead>";
      const body = document.createElement("tbody");
      const labels = ["Hisse", "Tahmin günü", "Hedef günü", "Tahmin olasılığı", "Gerçekleşen getiri", "Sonuç"];
      for (const row of rows) {
        const values = [row.symbol || "—", row.prediction_date || "—", row.target_date || "—", formatPercent((Number(row.probability_above_5) || 0) * 100), formatPercent(row.actual_change_percent), row.successful === true ? "Başarılı" : row.successful === false ? "Başarısız" : "Bekliyor"];
        const tr = document.createElement("tr");
        values.forEach((value, index) => {
          const cell = document.createElement("td");
          cell.textContent = value;
          cell.dataset.label = labels[index];
          if (index === 5) cell.className = "pill";
          if (index === 4 && row.actual_change_percent != null) cell.classList.add(Number(row.actual_change_percent) >= 0 ? "positive" : "negative");
          tr.append(cell);
        });
        body.append(tr);
      }
      table.append(body);
      history.append(table);
    } catch (_) {
      summary.textContent = "Gerçekleşen sonuçlara şu anda ulaşılamıyor.";
    }
  }

  document.querySelector("#refresh")?.addEventListener("click", loadTracking);
  document.querySelector("#prediction-date")?.addEventListener("change", loadTracking);
  if ("serviceWorker" in navigator) navigator.serviceWorker.register("/service-worker.js").catch(() => {});
  loadTracking();
})();
