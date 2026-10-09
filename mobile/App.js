import React, { useCallback, useEffect, useState } from "react";
import { ActivityIndicator, Pressable, RefreshControl, SafeAreaView, ScrollView, StatusBar, StyleSheet, Text, View } from "react-native";

const API_BASE = "__OLD_API_URL__";
const C = { bg: "#0b1220", panel: "#111b2b", line: "#263750", text: "#edf4ff", muted: "#9aacc4", green: "#38d39f", blue: "#7cb9ff", red: "#ff7c86" };
const pct = (v, d = 1) => v == null || !Number.isFinite(Number(v)) ? "—" : Number(v).toLocaleString("tr-TR", { maximumFractionDigits: d }) + "%";
const probability = v => pct(Number(v) * 100, 1);

function Forecast({ item }) {
  const positive = Number(item.expected_change_percent) >= 0;
  return <View style={s.card}>
    <View style={s.top}><View><Text style={s.symbol}>{item.symbol}</Text><Text style={s.muted}>Hedef gün · {item.target_date || "—"}</Text></View>
      <View style={s.badge}><Text style={s.prob}>{probability(item.probability_above_5)}</Text><Text style={s.muted}>+%5 olasılığı</Text></View></View>
    <View style={s.bottom}><Text style={s.muted}>Beklenen getiri</Text><Text style={[s.ret, { color: positive ? C.green : C.red }]}>{pct(item.expected_change_percent, 2)}</Text><Text style={s.muted}>Model güveni {probability(item.model_confidence)}</Text></View>
    {item.explanation ? <Text style={s.explanation}>{item.explanation}</Text> : null}
  </View>;
}

export default function App() {
  const [forecasts, setForecasts] = useState([]);
  const [predictionDate, setPredictionDate] = useState("");
  const [loading, setLoading] = useState(true);
  const [refreshing, setRefreshing] = useState(false);
  const [error, setError] = useState("");
  const load = useCallback(async (refresh = false) => {
    refresh ? setRefreshing(true) : setLoading(true);
    setError("");
    try {
      const response = await fetch(API_BASE + "/predictions?t=" + Date.now(), { headers: { Accept: "application/json", "Cache-Control": "no-cache" } });
      if (!response.ok) throw new Error("HTTP " + response.status);
      const data = await response.json();
      setForecasts(Array.isArray(data.predictions) ? data.predictions : []);
      setPredictionDate(data.prediction_date || "");
    } catch {
      setError("Eski sürüm sunucusuna ulaşılamadı. Sunucu adresini ve bağlantıyı kontrol et.");
    } finally { setLoading(false); setRefreshing(false); }
  }, []);
  useEffect(() => { load(); }, [load]);
  const avg = forecasts.length ? forecasts.reduce((sum, item) => sum + (Number(item.expected_change_percent) || 0), 0) / forecasts.length : null;
  return <SafeAreaView style={s.safe}><StatusBar barStyle="light-content" backgroundColor={C.bg}/>
    <View style={s.header}><View><Text style={s.title}>BIST Katılım</Text><Text style={s.subtitle}>2 Ekim 2026 sürüm karşılaştırması</Text></View><Pressable onPress={() => load(true)} style={s.refresh}><Text style={s.refreshText}>Yenile</Text></Pressable></View>
    <ScrollView contentContainerStyle={s.content} refreshControl={<RefreshControl refreshing={refreshing} onRefresh={() => load(true)} tintColor={C.green}/>}>
      <Text style={s.heading}>Eski model tahminleri</Text><Text style={s.muted}>Tahmin/veri tarihi · {predictionDate || "—"}</Text>
      <View style={s.stats}><View style={s.stat}><Text style={s.muted}>Tahmin adedi</Text><Text style={s.statValue}>{forecasts.length}</Text></View><View style={s.stat}><Text style={s.muted}>Ort. beklenen getiri</Text><Text style={s.statValue}>{pct(avg, 2)}</Text></View></View>
      {error ? <Text style={s.error}>{error}</Text> : null}
      {loading && !forecasts.length ? <ActivityIndicator color={C.green} style={{ marginTop: 30 }}/> : null}
      {!loading && !error && !forecasts.length ? <Text style={s.empty}>Sunucuda bu tarih için kayıtlı tahmin bulunamadı. Yeni tahmin üretildiği varsayılmayacak.</Text> : null}
      {forecasts.map(item => <Forecast key={item.symbol + item.target_date} item={item}/>)}
      <Text style={s.footer}>Bu uygulama yalnızca 2 Ekim sürümünün ayrı sunucusundan gelen kayıtları gösterir. Yatırım tavsiyesi değildir.</Text>
    </ScrollView>
  </SafeAreaView>;
}
const s = StyleSheet.create({
 safe:{flex:1,backgroundColor:C.bg}, header:{padding:18,paddingBottom:12,flexDirection:"row",alignItems:"center",justifyContent:"space-between"}, title:{color:C.text,fontSize:23,fontWeight:"800"},subtitle:{color:C.muted,marginTop:4},refresh:{backgroundColor:"#1b2c43",borderRadius:10,paddingVertical:10,paddingHorizontal:14},refreshText:{color:C.blue,fontWeight:"700"},content:{padding:16,paddingBottom:36},heading:{color:C.text,fontSize:19,fontWeight:"800",marginBottom:6},muted:{color:C.muted,fontSize:12},stats:{flexDirection:"row",gap:10,marginVertical:16},stat:{flex:1,backgroundColor:C.panel,borderColor:C.line,borderWidth:1,borderRadius:14,padding:14},statValue:{color:C.text,fontSize:20,fontWeight:"800",marginTop:8},card:{backgroundColor:C.panel,borderColor:C.line,borderWidth:1,borderRadius:16,padding:15,marginBottom:12},top:{flexDirection:"row",justifyContent:"space-between",alignItems:"center"},symbol:{color:C.text,fontSize:22,fontWeight:"800"},badge:{alignItems:"flex-end"},prob:{color:C.green,fontSize:18,fontWeight:"800"},bottom:{borderTopColor:C.line,borderTopWidth:1,marginTop:14,paddingTop:12,flexDirection:"row",alignItems:"center",justifyContent:"space-between",flexWrap:"wrap",gap:8},ret:{fontSize:18,fontWeight:"800"},explanation:{color:C.muted,fontSize:12,marginTop:10,lineHeight:18},error:{color:C.red,marginVertical:10},empty:{color:C.muted,marginTop:22,lineHeight:22},footer:{color:C.muted,fontSize:11,marginTop:16,lineHeight:17}
});
