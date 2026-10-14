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

  const learning = document.createElement("section");
  learning.style.marginTop = "28px";
  learning.innerHTML = '<h2 style="font-size:20px;margin:0 0 4px">Öğrenme modu ve örüntüler</h2><p style="margin:0 0 12px;color:#9aacc4;font-size:13px">Mod açıkken yeni öğrenme kayıtları alınır; kapalıyken tahmin taraması devam eder ama yeni örnekler öğrenme belleğine eklenmez.</p><button id="learning-toggle" type="button">Öğrenme durumu yükleniyor…</button> <span id="learning-control-status" role="status" style="color:#9aacc4;font-size:13px"></span><div style="height:12px"></div><button id="show-learning" type="button">Öğrenilen örüntüleri göster</button><p id="learning-summary" style="color:#9aacc4;font-size:13px"></p><div id="learning-pattern-results"></div>';
  tracking.after(learning);
  const learningToggle = learning.querySelector("#learning-toggle");
  const learningControlStatus = learning.querySelector("#learning-control-status");
  const showLearning = learning.querySelector("#show-learning");
  const learningSummary = learning.querySelector("#learning-summary");
  const learningResults = learning.querySelector("#learning-pattern-results");
  let learningEnabled = null;

  function renderLearningControl() {
    learningToggle.textContent = learningEnabled ? "Öğrenme modunu kapat" : "Öğrenme modunu aç";
    learningToggle.setAttribute("aria-pressed", learningEnabled ? "true" : "false");
    learningControlStatus.textContent = learningEnabled ? "Durum: Açık" : "Durum: Kapalı";
  }

  async function loadLearningControl() {
    learningToggle.disabled = true;
    try {
      const response = await fetch("/learning-control", {headers:{Accept:"application/json"}, cache:"no-store"});
      if (!response.ok) throw new Error("Unavailable");
      const data = await response.json();
      learningEnabled = data.enabled === true;
      renderLearningControl();
    } catch (_) {
      learningToggle.textContent = "Öğrenme durumu alınamadı";
      learningControlStatus.textContent = "API bağlantısını kontrol edin.";
    } finally {
      learningToggle.disabled = false;
    }
  }

  learningToggle.addEventListener("click", async () => {
    if (learningEnabled === null) return;
    const desired = !learningEnabled;
    learningToggle.disabled = true;
    learningControlStatus.textContent = "Kaydediliyor…";
    try {
      const response = await fetch("/learning-control?enabled=" + String(desired), {
        method:"POST",
        headers:{Accept:"application/json"},
        cache:"no-store"
      });
      if (!response.ok) throw new Error("Unavailable");
      const data = await response.json();
      learningEnabled = data.enabled === true;
      renderLearningControl();
      learningControlStatus.textContent = learningEnabled
        ? "Öğrenme açıldı; yeni uygun örnekler kaydedilebilir."
        : "Öğrenme kapatıldı; tahmin taraması devam eder.";
    } catch (_) {
      learningControlStatus.textContent = "Değişiklik uygulanamadı. Bağlantıyı kontrol edip tekrar deneyin.";
    } finally {
      learningToggle.disabled = false;
    }
  });

  loadLearningControl();

  showLearning.addEventListener("click", async () => {
    showLearning.disabled = true;
    learningSummary.textContent = "Öğrenme kayıtları yükleniyor…";
    try {
      const response = await fetch("/learning-patterns?limit=100", {headers:{Accept:"application/json"}});
      if (!response.ok) throw new Error("Unavailable");
      const data = await response.json();
      learningSummary.textContent = "Öğrenilmiş örnek: " + (data.sample_count || 0) +
        " · Ortalama sonraki günlük yükseliş: " +
        (data.average_signal_return_percent == null ? "—" : Number(data.average_signal_return_percent).toLocaleString("tr-TR", {maximumFractionDigits:2}) + "%");
      learningResults.replaceChildren();
      const indicators = data.average_prior_day_indicators || {};
      const indicatorNames = Object.keys(indicators);
      if (indicatorNames.length) {
        const heading = document.createElement("h3");
        heading.textContent = "Örneklerde ortalama önceki gün göstergeleri";
        heading.style.fontSize = "15px";
        learningResults.append(heading);
        const list = document.createElement("p");
        list.style.color = "#9aacc4";
        list.textContent = indicatorNames.map(name => name + ": " + Number(indicators[name]).toLocaleString("tr-TR", {maximumFractionDigits:3})).join(" · ");
        learningResults.append(list);
      }
      const events = Array.isArray(data.events) ? data.events : [];
      if (!events.length) {
        const empty = document.createElement("div");
        empty.className = "empty";
        empty.textContent = "Henüz öğrenme kaydı bulunmuyor. Gün sonu taraması tamamlandıktan sonra tekrar kontrol edin.";
        learningResults.append(empty);
      } else {
        const table = document.createElement("table");
        table.innerHTML = "<thead><tr><th>Hisse</th><th>Referans günü</th><th>Yükseliş günü</th><th>Gerçek yükseliş</th><th>Önceki gün göstergeleri</th></tr></thead>";
        const body = document.createElement("tbody");
        for (const event of events) {
          const tr = document.createElement("tr");
          const values = [
            event.symbol || "—",
            event.reference_date || "—",
            event.signal_date || "—",
            event.rise_percent == null ? "—" : Number(event.rise_percent).toLocaleString("tr-TR", {maximumFractionDigits:2}) + "%",
            Object.entries(event.technical_features || {}).map(([key,value]) => key + ": " + (typeof value === "number" ? value.toLocaleString("tr-TR", {maximumFractionDigits:3}) : String(value))).join(" · ") || "—"
          ];
          values.forEach((value,index) => {
            const td = document.createElement("td");
            td.textContent = value;
            td.dataset.label = ["Hisse","Referans günü","Yükseliş günü","Gerçek yükseliş","Önceki gün göstergeleri"][index];
            if (index === 0) td.className = "symbol";
            tr.append(td);
          });
          body.append(tr);
        }
        table.append(body);
        const wrap = document.createElement("div");
        wrap.className = "table-wrap";
        wrap.style.overflowX = "auto";
        wrap.append(table);
        learningResults.append(wrap);
      }
    } catch (_) {
      learningSummary.textContent = "Öğrenme örüntülerine şu anda ulaşılamıyor.";
    } finally {
      showLearning.disabled = false;
    }
  });

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
