import React, { useCallback, useEffect, useMemo, useState } from "react";
import {
  ActivityIndicator,
  Pressable,
  RefreshControl,
  SafeAreaView,
  ScrollView,
  StatusBar,
  StyleSheet,
  Text,
  View,
} from "react-native";

const API_BASE = "https://bist-katilim-ai-predictor-api.onrender.com";
const COLORS = {
  background: "#0b1220",
  panel: "#111b2b",
  panelAlt: "#101a2a",
  line: "#263750",
  text: "#edf4ff",
  muted: "#9aacc4",
  green: "#38d39f",
  blue: "#7cb9ff",
  red: "#ff7c86",
};

const formatPercent = (value, digits = 1) => {
  if (value == null || !Number.isFinite(Number(value))) return "—";
  return Number(value).toLocaleString("tr-TR", { maximumFractionDigits: digits }) + "%";
};

const formatProbability = (value) => formatPercent(Number(value) * 100, 1);
const formatReturn = (value) => formatPercent(value, 2);

function StatCard({ label, value, note }) {
  return (
    <View style={styles.statCard}>
      <Text style={styles.statLabel}>{label}</Text>
      <Text style={styles.statValue}>{value}</Text>
      {note ? <Text style={styles.statNote}>{note}</Text> : null}
    </View>
  );
}

function ForecastCard({ item }) {
  const positive = Number(item.expected_change_percent) >= 0;
  return (
    <View style={styles.forecastCard}>
      <View style={styles.forecastTop}>
        <View>
          <Text style={styles.symbol}>{item.symbol}</Text>
          <Text style={styles.muted}>Hedef gün · {item.target_date || "—"}</Text>
        </View>
        <View style={styles.probabilityBadge}>
          <Text style={styles.probability}>{formatProbability(item.probability_above_5)}</Text>
          <Text style={styles.badgeCaption}>+%5 olasılığı</Text>
        </View>
      </View>
      <View style={styles.forecastBottom}>
        <Text style={styles.muted}>Beklenen getiri</Text>
        <Text style={[styles.returnValue, { color: positive ? COLORS.green : COLORS.red }]}>
          {formatReturn(item.expected_change_percent)}
        </Text>
        <Text style={styles.confidence}>
          Model güveni {formatProbability(item.model_confidence)}
        </Text>
      </View>
    </View>
  );
}

function OutcomeCard({ item }) {
  const result = item.successful === true ? "Başarılı" : item.successful === false ? "Başarısız" : "Bekliyor";
  const color = item.successful === true ? COLORS.green : item.successful === false ? COLORS.red : COLORS.muted;
  return (
    <View style={styles.outcomeCard}>
      <View style={styles.outcomeTop}>
        <Text style={styles.symbol}>{item.symbol}</Text>
        <Text style={[styles.outcomeStatus, { color }]}>{result}</Text>
      </View>
      <Text style={styles.muted}>Tahmin {item.prediction_date}  ·  Hedef {item.target_date}</Text>
      <View style={styles.outcomeBottom}>
        <Text style={styles.muted}>+%5 olasılığı {formatProbability(item.probability_above_5)}</Text>
        <Text style={[styles.returnValue, { color: item.actual_change_percent == null ? COLORS.muted : Number(item.actual_change_percent) >= 0 ? COLORS.green : COLORS.red }]}>
          Gerçekleşen {formatReturn(item.actual_change_percent)}
        </Text>
      </View>
    </View>
  );
}

export default function App() {
  const [screen, setScreen] = useState("forecasts");
  const [forecasts, setForecasts] = useState([]);
  const [performance, setPerformance] = useState(null);
  const [loading, setLoading] = useState(true);
  const [refreshing, setRefreshing] = useState(false);
  const [error, setError] = useState("");

  const load = useCallback(async (isRefresh = false) => {
    if (isRefresh) setRefreshing(true);
    else setLoading(true);
    setError("");
    const results = await Promise.allSettled([
      fetch(API_BASE + "/predictions", { headers: { Accept: "application/json" } }),
      fetch(API_BASE + "/performance?limit=30", { headers: { Accept: "application/json" } }),
    ]);
    let failures = 0;
    if (results[0].status === "fulfilled" && results[0].value.ok) {
      const data = await results[0].value.json();
      setForecasts(Array.isArray(data.predictions) ? data.predictions : []);
    } else {
      failures += 1;
    }
    if (results[1].status === "fulfilled" && results[1].value.ok) {
      setPerformance(await results[1].value.json());
    } else {
      failures += 1;
    }
    if (failures === 2) setError("Sunucuya ulaşılamadı. Bağlantını kontrol edip yeniden dene.");
    else if (failures === 1) setError("Bazı veriler yüklenemedi. Yenile ile tekrar deneyebilirsin.");
    setLoading(false);
    setRefreshing(false);
  }, []);

  useEffect(() => { load(); }, [load]);

  const averageReturn = useMemo(() => {
    if (!forecasts.length) return null;
    return forecasts.reduce((sum, item) => sum + (Number(item.expected_change_percent) || 0), 0) / forecasts.length;
  }, [forecasts]);

  const trackingRows = performance?.predictions || [];

  return (
    <SafeAreaView style={styles.safe}>
      <StatusBar barStyle="light-content" backgroundColor={COLORS.background} />
      <View style={styles.header}>
        <View style={styles.brand}>
          <View style={styles.brandMark}><Text style={styles.brandLetter}>B</Text></View>
          <View>
            <Text style={styles.title}>BIST Katılım</Text>
            <Text style={styles.subtitle}>Gün sonu tahminleri</Text>
          </View>
        </View>
        <Pressable onPress={() => load(true)} accessibilityRole="button" style={styles.refreshButton}>
          <Text style={styles.refreshText}>Yenile</Text>
        </Pressable>
      </View>

      <View style={styles.tabs}>
        <Pressable onPress={() => setScreen("forecasts")} style={[styles.tab, screen === "forecasts" && styles.activeTab]}>
          <Text style={[styles.tabText, screen === "forecasts" && styles.activeTabText]}>Tahminler</Text>
        </Pressable>
        <Pressable onPress={() => setScreen("tracking")} style={[styles.tab, screen === "tracking" && styles.activeTab]}>
          <Text style={[styles.tabText, screen === "tracking" && styles.activeTabText]}>Sonuç takibi</Text>
        </Pressable>
      </View>

      {error ? <Text accessibilityRole="alert" style={styles.error}>{error}</Text> : null}

      <ScrollView
        contentContainerStyle={styles.content}
        refreshControl={<RefreshControl refreshing={refreshing} onRefresh={() => load(true)} tintColor={COLORS.green} />}
      >
        {screen === "forecasts" ? (
          <>
            <Text style={styles.sectionTitle}>En yüksek +%5 olasılığı</Text>
            <Text style={styles.sectionHint}>Model olasılıklarına göre sıralanmıştır; getiri garantisi değildir.</Text>
            <View style={styles.stats}>
              <StatCard label="Tahmin adedi" value={String(forecasts.length)} />
              <StatCard label="Ort. beklenen getiri" value={formatReturn(averageReturn)} />
            </View>
            {loading && forecasts.length === 0 ? <ActivityIndicator color={COLORS.green} style={styles.loader} /> : null}
            {!loading && forecasts.length === 0 ? <Text style={styles.empty}>Şu an gösterilecek tahmin yok.</Text> : null}
            {forecasts.map((item) => <ForecastCard key={item.symbol + item.target_date} item={item} />)}
          </>
        ) : (
          <>
            <Text style={styles.sectionTitle}>Tahmin sonuçları</Text>
            <Text style={styles.sectionHint}>Hedef işlem günü kapandıktan sonra gerçek değişim ve isabet oranı güncellenir.</Text>
            <View style={styles.stats}>
              <StatCard
                label="Gerçekleşen +%5 isabeti"
                value={performance?.hit_rate_percent == null ? "Ölçülüyor" : formatPercent(performance.hit_rate_percent)}
                note={performance ? performance.evaluated_count + " sonuç değerlendirildi" : ""}
              />
              <StatCard label="Bekleyen tahmin" value={String(performance?.pending_count ?? "—")} />
            </View>
            {loading && trackingRows.length === 0 ? <ActivityIndicator color={COLORS.green} style={styles.loader} /> : null}
            {!loading && trackingRows.length === 0 ? <Text style={styles.empty}>Takip edilecek tahmin henüz yok.</Text> : null}
            {trackingRows.map((item, index) => <OutcomeCard key={item.symbol + item.prediction_date + index} item={item} />)}
          </>
        )}
        <View style={styles.notice}>
          <Text style={styles.noticeTitle}>Bilgilendirme</Text>
          <Text style={styles.noticeText}>Olasılık tahmindir, garanti değildir. Uygulama alım-satım yapmaz. Sonuçlar günlük kapanış verileriyle takip edilir.</Text>
        </View>
        <Text style={styles.updated}>Veri kaynağı: mevcut BIST Katılım tahmin API’si</Text>
      </ScrollView>
    </SafeAreaView>
  );
}

const styles = StyleSheet.create({
  safe: { flex: 1, backgroundColor: COLORS.background },
  header: { paddingHorizontal: 18, paddingTop: 12, paddingBottom: 16, flexDirection: "row", alignItems: "center", justifyContent: "space-between" },
  brand: { flexDirection: "row", alignItems: "center", gap: 11 },
  brandMark: { width: 42, height: 42, borderRadius: 14, backgroundColor: "#143a3a", alignItems: "center", justifyContent: "center" },
  brandLetter: { color: COLORS.green, fontWeight: "900", fontSize: 20 },
  title: { color: COLORS.text, fontSize: 21, fontWeight: "800" },
  subtitle: { color: COLORS.muted, fontSize: 12, marginTop: 2 },
  refreshButton: { backgroundColor: "#137a61", borderRadius: 11, paddingHorizontal: 14, paddingVertical: 10 },
  refreshText: { color: "#ffffff", fontWeight: "700", fontSize: 13 },
  tabs: { marginHorizontal: 18, flexDirection: "row", backgroundColor: COLORS.panelAlt, padding: 4, borderRadius: 13, borderWidth: 1, borderColor: COLORS.line },
  tab: { flex: 1, alignItems: "center", paddingVertical: 10, borderRadius: 10 },
  activeTab: { backgroundColor: "#137a61" },
  tabText: { color: COLORS.muted, fontWeight: "650", fontSize: 13 },
  activeTabText: { color: "#ffffff" },
  content: { paddingHorizontal: 18, paddingTop: 22, paddingBottom: 36 },
  sectionTitle: { color: COLORS.text, fontWeight: "800", fontSize: 19 },
  sectionHint: { color: COLORS.muted, fontSize: 12, lineHeight: 18, marginTop: 5, marginBottom: 16 },
  stats: { flexDirection: "row", gap: 10, marginBottom: 14 },
  statCard: { flex: 1, minHeight: 90, padding: 13, borderRadius: 14, borderWidth: 1, borderColor: COLORS.line, backgroundColor: COLORS.panel },
  statLabel: { color: COLORS.muted, fontSize: 11, lineHeight: 16 },
  statValue: { color: COLORS.text, fontSize: 20, fontWeight: "800", marginTop: 6 },
  statNote: { color: COLORS.muted, fontSize: 10, marginTop: 2 },
  forecastCard: { padding: 15, backgroundColor: COLORS.panel, borderColor: COLORS.line, borderWidth: 1, borderRadius: 16, marginBottom: 11 },
  forecastTop: { flexDirection: "row", alignItems: "center", justifyContent: "space-between" },
  symbol: { color: COLORS.blue, fontSize: 18, fontWeight: "800" },
  muted: { color: COLORS.muted, fontSize: 11, marginTop: 3 },
  probabilityBadge: { backgroundColor: "#16383a", borderRadius: 12, paddingVertical: 7, paddingHorizontal: 11, alignItems: "center" },
  probability: { color: COLORS.green, fontWeight: "800", fontSize: 16 },
  badgeCaption: { color: COLORS.muted, fontSize: 9, marginTop: 1 },
  forecastBottom: { borderTopWidth: 1, borderTopColor: COLORS.line, marginTop: 13, paddingTop: 11, flexDirection: "row", alignItems: "center", gap: 7, flexWrap: "wrap" },
  returnValue: { fontSize: 13, fontWeight: "800" },
  confidence: { marginLeft: "auto", color: COLORS.muted, fontSize: 10 },
  outcomeCard: { padding: 14, backgroundColor: COLORS.panel, borderColor: COLORS.line, borderWidth: 1, borderRadius: 15, marginBottom: 10 },
  outcomeTop: { flexDirection: "row", justifyContent: "space-between", alignItems: "center" },
  outcomeStatus: { fontWeight: "750", fontSize: 12 },
  outcomeBottom: { borderTopWidth: 1, borderTopColor: COLORS.line, marginTop: 10, paddingTop: 9, flexDirection: "row", justifyContent: "space-between", alignItems: "center", flexWrap: "wrap", gap: 5 },
  notice: { padding: 14, borderRadius: 14, borderWidth: 1, borderColor: "#4b4130", backgroundColor: "#211e19", marginTop: 10 },
  noticeTitle: { color: "#f3ca77", fontWeight: "800", fontSize: 12 },
  noticeText: { color: COLORS.muted, fontSize: 11, lineHeight: 17, marginTop: 4 },
  updated: { textAlign: "center", color: COLORS.muted, fontSize: 10, marginTop: 14 },
  empty: { color: COLORS.muted, backgroundColor: COLORS.panel, borderColor: COLORS.line, borderWidth: 1, borderRadius: 14, padding: 22, textAlign: "center", fontSize: 13 },
  error: { marginHorizontal: 18, marginTop: 10, color: COLORS.red, fontSize: 12 },
  loader: { marginVertical: 32 },
});
