import { useState } from "react";
import {
  ActivityIndicator,
  Image,
  Pressable,
  ScrollView,
  StyleSheet,
  Text,
  TextInput,
  View,
} from "react-native";
import { StatusBar } from "expo-status-bar";
import * as ImagePicker from "expo-image-picker";
import {
  login,
  measure,
  signup,
  type AuthSession,
  type Calibration,
  type MeasureResult,
} from "./src/api";

const FINGERS: { key: keyof MeasureResult["hand"]; label: string }[] = [
  { key: "index_jp_size", label: "人差し指" },
  { key: "middle_jp_size", label: "中指" },
  { key: "ring_jp_size", label: "薬指" },
  { key: "pinky_jp_size", label: "小指" },
];

export default function App() {
  const [session, setSessionState] = useState<AuthSession | null>(null);
  const [name, setName] = useState("");
  const [password, setPassword] = useState("");
  const [imageUri, setImageUri] = useState<string | null>(null);
  const [result, setResult] = useState<MeasureResult | null>(null);
  const [busy, setBusy] = useState(false);
  const [error, setError] = useState<string | null>(null);

  function auth(mode: "login" | "signup") {
    setBusy(true);
    setError(null);
    (mode === "login" ? login : signup)(name.trim(), password)
      .then(setSessionState)
      .catch((e: unknown) => setError(e instanceof Error ? e.message : String(e)))
      .finally(() => setBusy(false));
  }

  async function pickAndMeasure() {
    if (!session) return;
    const picked = await ImagePicker.launchImageLibraryAsync({ quality: 0.8 });
    if (picked.canceled) return;
    const uri = picked.assets[0].uri;
    setImageUri(uri);
    setBusy(true);
    setError(null);
    const cal: Calibration = { kind: "card" };
    measure(session.user_id, uri, cal)
      .then(setResult)
      .catch((e: unknown) => setError(e instanceof Error ? e.message : String(e)))
      .finally(() => setBusy(false));
  }

  return (
    <ScrollView contentContainerStyle={styles.container}>
      <StatusBar style="dark" />
      <Text style={styles.brand}>KIRAKU</Text>
      <Text style={styles.h1}>指号数計測</Text>

      {error && <Text style={styles.error}>{error}</Text>}

      {!session ? (
        <View style={styles.card}>
          <TextInput style={styles.field} placeholder="ユーザー名" value={name} onChangeText={setName} autoCapitalize="none" />
          <TextInput style={styles.field} placeholder="パスワード" value={password} onChangeText={setPassword} secureTextEntry />
          <Pressable style={styles.btnPrimary} onPress={() => auth("signup")} disabled={busy}>
            <Text style={styles.btnPrimaryText}>登録してはじめる</Text>
          </Pressable>
          <Pressable style={styles.btn} onPress={() => auth("login")} disabled={busy}>
            <Text>ログイン</Text>
          </Pressable>
        </View>
      ) : (
        <View style={styles.card}>
          <Text style={styles.muted}>{session.user_name} としてログイン中</Text>
          <Pressable style={styles.btnPrimary} onPress={pickAndMeasure} disabled={busy}>
            <Text style={styles.btnPrimaryText}>手の写真を選んで計測（カード基準）</Text>
          </Pressable>
        </View>
      )}

      {busy && <ActivityIndicator style={{ marginTop: 16 }} />}

      {imageUri && <Image source={{ uri: imageUri }} style={styles.preview} resizeMode="contain" />}

      {result && (
        <View style={styles.card}>
          <Text style={styles.h2}>計測結果</Text>
          <View style={styles.row}>
            {FINGERS.map((f) => (
              <View key={f.key} style={styles.fingerCol}>
                <Text style={styles.muted}>{f.label}</Text>
                <Text style={styles.size}>{result.hand[f.key]}号</Text>
              </View>
            ))}
          </View>
        </View>
      )}
    </ScrollView>
  );
}

const styles = StyleSheet.create({
  container: { padding: 20, paddingTop: 64, backgroundColor: "#f3ecdd", minHeight: "100%" },
  brand: { letterSpacing: 6, color: "#9c7c43", fontWeight: "600" },
  h1: { fontSize: 26, marginVertical: 12, color: "#2b2620" },
  h2: { fontSize: 18, marginBottom: 10, color: "#2b2620" },
  muted: { color: "#6f6558", marginBottom: 8 },
  error: { color: "#9b3b30", marginBottom: 12 },
  card: {
    backgroundColor: "rgba(255,255,255,0.65)",
    borderRadius: 20,
    padding: 18,
    marginTop: 14,
    borderWidth: 1,
    borderColor: "rgba(255,255,255,0.8)",
  },
  field: {
    backgroundColor: "rgba(255,255,255,0.7)",
    borderRadius: 12,
    borderWidth: 1,
    borderColor: "rgba(176,152,110,0.4)",
    padding: 12,
    marginBottom: 10,
  },
  btn: { padding: 12, alignItems: "center", borderRadius: 999, marginTop: 8 },
  btnPrimary: {
    backgroundColor: "#b9975b",
    padding: 14,
    alignItems: "center",
    borderRadius: 999,
    marginTop: 6,
  },
  btnPrimaryText: { color: "#fffdf8", fontWeight: "600" },
  preview: { width: "100%", height: 220, marginTop: 14, borderRadius: 16 },
  row: { flexDirection: "row", justifyContent: "space-between" },
  fingerCol: { alignItems: "center", flex: 1 },
  size: { fontSize: 26, color: "#9c7c43", fontWeight: "700" },
});
