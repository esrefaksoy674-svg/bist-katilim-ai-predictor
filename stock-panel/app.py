from fastapi import FastAPI, HTTPException
from fastapi.responses import FileResponse
from fastapi.middleware.cors import CORSMiddleware
from pathlib import Path
import math
import yfinance as yf
import pandas as pd

BASE = Path(__file__).resolve().parent
app = FastAPI(title="BIST Hisse Analiz Paneli", version="1.0.0")
app.add_middleware(CORSMiddleware, allow_origins=["*"], allow_methods=["*"], allow_headers=["*"])

@app.get("/")
def home():
    return FileResponse(BASE / "index.html")

def num(v):
    try:
        x = float(v)
        return round(x, 3) if math.isfinite(x) else None
    except Exception:
        return None

@app.get("/api/health")
def health():
    return {"ok": True, "service": "stock-analysis-panel"}

@app.get("/api/analyze/{ticker}")
def analyze(ticker: str):
    symbol = ticker.strip().upper().replace(".IS", "")
    if not symbol or len(symbol) > 12 or not symbol.replace(".", "").isalnum():
        raise HTTPException(status_code=400, detail="Geçerli bir BIST hisse kodu girin.")
    try:
        df = yf.download(symbol + ".IS", period="1y", interval="1d", auto_adjust=False, progress=False, threads=False)
        if df is None or df.empty:
            raise HTTPException(status_code=404, detail="Bu kod için veri bulunamadı. Sembolü kontrol edin.")
        if isinstance(df.columns, pd.MultiIndex):
            df.columns = df.columns.get_level_values(0)
        df = df.dropna(subset=["Close"])
        if len(df) < 30:
            raise HTTPException(status_code=422, detail="Yeterli geçmiş veri yok; gösterge hesaplanamadı.")
        close = df["Close"].astype(float)
        high = df["High"].astype(float) if "High" in df else close
        low = df["Low"].astype(float) if "Low" in df else close
        volume = df["Volume"].astype(float) if "Volume" in df else pd.Series(index=df.index, data=[0]*len(df))
        delta = close.diff()
        gain = delta.clip(lower=0).rolling(14).mean()
        loss = (-delta.clip(upper=0)).rolling(14).mean()
        rs = gain / loss.replace(0, float("nan"))
        rsi_series = 100 - (100 / (1 + rs))
        rsi = float(rsi_series.iloc[-1]) if pd.notna(rsi_series.iloc[-1]) else (100.0 if loss.iloc[-1] == 0 else 50.0)
        ema12 = close.ewm(span=12, adjust=False).mean()
        ema26 = close.ewm(span=26, adjust=False).mean()
        macd = ema12 - ema26
        signal = macd.ewm(span=9, adjust=False).mean()
        ema20 = close.ewm(span=20, adjust=False).mean()
        ema50 = close.ewm(span=50, adjust=False).mean()
        last = float(close.iloc[-1])
        prev = float(close.iloc[-2])
        chg = ((last / prev) - 1) * 100 if prev else 0
        avgvol = float(volume.tail(20).mean()) if len(volume) else 0
        volratio = float(volume.iloc[-1] / avgvol) if avgvol else None
        support = float(low.tail(20).min())
        resistance = float(high.tail(20).max())
        macd_hist = float((macd - signal).iloc[-1])
        score = 0
        score += 1 if rsi < 68 else -1 if rsi > 75 else 0
        score += 1 if last > float(ema20.iloc[-1]) else -1
        score += 1 if float(ema20.iloc[-1]) > float(ema50.iloc[-1]) else -1
        score += 1 if macd_hist > 0 else -1
        score += 1 if volratio is not None and volratio > 1.2 and chg > 0 else 0
        if score >= 3:
            decision, note = "AL sinyali", "Teknik göstergelerin çoğu olumlu; tek başına alım garantisi değildir."
        elif score <= -2:
            decision, note = "SAT / RİSKİ AZALT", "Teknik görünüm zayıf; karar vermeden riskinizi değerlendirin."
        else:
            decision, note = "BEKLE", "Göstergeler karışık; teyit beklemek daha temkinli olabilir."
        # Heuristic levels only; never send orders.
        stop = max(0.01, min(last * 0.97, support * 0.985))
        target1 = last * 1.03
        target2 = last * 1.06
        return {
            "ticker": symbol, "name": symbol, "currency": "TRY",
            "last": num(last), "change_pct": num(chg), "date": str(df.index[-1].date()),
            "data_note": "Yahoo Finance üzerinden günlük geçmiş fiyatlar; gecikmeli olabilir. Canlı fiyat garantisi yoktur.",
            "indicators": {
                "RSI_14": num(rsi), "MACD": num(macd.iloc[-1]), "MACD_signal": num(signal.iloc[-1]),
                "MACD_histogram": num(macd_hist), "EMA20": num(ema20.iloc[-1]), "EMA50": num(ema50.iloc[-1]),
                "volume": num(volume.iloc[-1]), "volume_vs_20d": num(volratio),
                "support_20d": num(support), "resistance_20d": num(resistance)
            },
            "decision": decision, "score": score, "comment": note,
            "levels": {"reference": num(last), "stop_loss_illustrative": num(stop),
                       "target_1_illustrative": num(target1), "target_2_illustrative": num(target2)},
            "disclaimer": "Bilgilendirme amaçlı otomatik teknik hesaplamadır; yatırım tavsiyesi değildir. Destek/direnç ve hedefler yaklaşık seviyelerdir."
        }
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=502, detail="Veri sağlayıcısından fiyat alınamadı. Biraz sonra yeniden deneyin.")
