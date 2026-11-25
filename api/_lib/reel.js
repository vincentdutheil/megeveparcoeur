// Publication de Reels Instagram en direct (API Instagram avec Facebook Login), avec musique et identifications.
// Utilise l'accès enregistré par le bouton « Connecter Instagram » de l'admin (Redis ig:auth).
// L'autorisation Facebook doit inclure instagram_basic + instagram_content_publish.
//
//   GET /api/reel?audio=<recherche>   → titres de la bibliothèque musicale disponibles via l'API (pour trouver audio_id)
//   GET /api/reel?key=<clé>           → publie le Reel décrit dans instagram/reels/<clé>.json (dépôt GitHub, branche main)
//
// Sécurité : seul un Reel déjà enregistré dans le dépôt (donc poussé par Vincent ou ses tâches) peut être publié,
// une seule fois (état dans Redis reel:<clé>), et pas avant son heure « after ».
// Fichier JSON : { "video": "https://www.megeveparcoeur.fr/instagram/....mp4", "caption": "...",
//   "audio_id": "123" | null, "audio_query": "Megève c'est le rêve Akhilleus", "audio_title": "Megève c'est le rêve",
//   "tags": ["megeve_officiel", ...], "cover": "https://.../cover.jpg", "thumb_offset": 1000,
//   "audio_volume": 100, "video_volume": 0, "after": "2026-11-22T09:00:00+01:00", "require_audio": true,
//   "location_id": "24274852196", "comment": "premier commentaire (facultatif)" }
const OWNER = "vincentdutheil", REPO = "megeveparcoeur";
const V = process.env.META_GRAPH_VERSION || "v23.0", GRAPH = "https://graph.facebook.com/" + V;
const RURL = process.env.KV_REST_API_URL || process.env.UPSTASH_REDIS_REST_URL;
const RTOK = process.env.KV_REST_API_TOKEN || process.env.UPSTASH_REDIS_REST_TOKEN;

async function redis(...cmd) {
  const r = await fetch(RURL, { method: "POST", headers: { Authorization: "Bearer " + RTOK, "Content-Type": "application/json" }, body: JSON.stringify(cmd) });
  const j = await r.json(); if (j.error) throw new Error(j.error); return j.result;
}
async function graph(path, params = {}, method = "GET") {
  const u = new URL(GRAPH + path);
  const body = new URLSearchParams();
  Object.entries(params).forEach(([k, v]) => { if (v == null) return; (method === "GET" ? u.searchParams : body).set(k, typeof v === "object" ? JSON.stringify(v) : String(v)); });
  const r = await fetch(u, method === "GET" ? {} : { method, body });
  const j = await r.json().catch(() => ({}));
  if (!r.ok || j.error) throw Object.assign(new Error((j.error && (j.error.error_user_msg || j.error.message)) || "graph " + r.status), { meta: j.error });
  return j;
}
const sleep = ms => new Promise(r => setTimeout(r, ms));
const norm = s => String(s || "").normalize("NFD").replace(/[̀-ͯ]/g, "").toLowerCase().replace(/[^a-z0-9]+/g, " ").trim();

async function searchAudio(auth, q) {
  const tok = auth.userToken || auth.pageToken;
  const j = await graph("/ig_audio", { audio_type: "music", user_id: auth.igId, search_query: q, access_token: tok });
  return (j.audio || j.data || []).map(a => ({ audio_id: a.audio_id || a.id, title: a.title, artist: a.display_artist, duration_ms: a.duration_in_ms, link: a.on_platform_audio_preview_link }));
}

module.exports = async (req, res) => {
  const send = (c, o) => { res.statusCode = c; res.setHeader("Content-Type", "application/json; charset=utf-8"); res.setHeader("Cache-Control", "no-store"); res.end(JSON.stringify(o)); };
  try {
    const url = new URL(req.url, "https://www.megeveparcoeur.fr");
    const s = await redis("GET", "ig:auth"); const auth = s ? JSON.parse(s) : null;
    if (!auth) return send(503, { ok: false, error: "Instagram n'est pas connecté (admin → Identifications → Connecter Instagram)" });

    if (url.searchParams.has("diag")) {
      let perms = null;
      try {
        const app = process.env.META_APP_ID + "|" + process.env.META_APP_SECRET;
        const d = await graph("/debug_token", { input_token: auth.userToken || auth.pageToken, access_token: app });
        perms = d.data && d.data.scopes;
      } catch (e) { perms = "erreur : " + e.message; }
      return send(200, { ok: true, connected_at: auth.at, username: auth.username, userToken: !!auth.userToken, perms });
    }
    if (url.searchParams.has("meta")) {
      const id = (url.searchParams.get("meta") || "").replace(/\D/g, "");
      const u = new URL(`${GRAPH}/${id}`);
      u.search = new URLSearchParams({ user_id: auth.igId, access_token: auth.userToken || auth.pageToken });
      const r2 = await fetch(u); const t = await r2.text();
      return send(200, { ok: r2.ok, status: r2.status, body: t.slice(0, 1500) });
    }
    if (url.searchParams.has("raw")) {
      const ver = url.searchParams.get("v") || V, type = url.searchParams.get("type") || "music";
      const tok = url.searchParams.get("tok") === "page" ? auth.pageToken : (auth.userToken || auth.pageToken);
      const u = new URL(`https://graph.facebook.com/${ver}/ig_audio`);
      u.search = new URLSearchParams({ audio_type: type, user_id: auth.igId, access_token: tok, ...(url.searchParams.get("q") ? { search_query: url.searchParams.get("q") } : {}) });
      const r2 = await fetch(u); const t = await r2.text();
      return send(200, { ok: true, status: r2.status, body: t.slice(0, 1500) });
    }
    if (url.searchParams.has("audio")) {
      const q = (url.searchParams.get("audio") || "").slice(0, 100);
      return send(200, { ok: true, query: q, results: await searchAudio(auth, q) });
    }

    const key = url.searchParams.get("key") || "";
    if (!/^[a-z0-9-]{3,60}$/.test(key)) return send(400, { ok: false, error: "clé invalide" });
    const r = await fetch(`https://raw.githubusercontent.com/${OWNER}/${REPO}/main/instagram/reels/${key}.json?t=${Date.now()}`);
    if (!r.ok) return send(404, { ok: false, error: "instagram/reels/" + key + ".json introuvable sur main" });
    const c = await r.json();
    if (!/^https:\/\/(www\.)?megeveparcoeur\.fr\//.test(c.video || "")) return send(400, { ok: false, error: "la vidéo doit être hébergée sur megeveparcoeur.fr" });
    if (c.after && Date.now() < Date.parse(c.after)) return send(425, { ok: false, error: "trop tôt : publication prévue après " + c.after });

    const st = JSON.parse((await redis("GET", "reel:" + key)) || "{}");
    if (st.published) return send(200, { ok: true, already: true, ...st });

    if (!st.container) {
      let audioId = c.audio_id || null, audioInfo = null;
      if (!audioId && c.audio_query) {
        const hits = await searchAudio(auth, c.audio_query);
        const want = norm(c.audio_title || c.audio_query);
        const m = hits.find(h => norm(h.title) === want) || hits.find(h => norm(h.title).includes(want));
        if (m) { audioId = m.audio_id; audioInfo = m; }
        else if (c.require_audio !== false) return send(424, { ok: false, error: "musique introuvable via l'API", query: c.audio_query, results: hits.slice(0, 10) });
      }
      const params = {
        media_type: "REELS", video_url: c.video, caption: c.caption || "", share_to_feed: "true",
        location_id: c.location_id || null,
        user_tags: (c.tags || []).length ? (c.tags || []).map(u => ({ username: String(u).replace(/^@/, "") })) : null,
        cover_url: c.cover || null, thumb_offset: c.cover ? null : (c.thumb_offset != null ? c.thumb_offset : null),
        audio_configuration: audioId ? { audio_id: String(audioId), audio_volume: c.audio_volume ?? 100, video_volume: c.video_volume ?? 0 } : null,
        access_token: auth.pageToken,
      };
      const ct = await graph(`/${auth.igId}/media`, params, "POST");
      Object.assign(st, { container: ct.id, audio: audioInfo || (audioId ? { audio_id: audioId } : null), created: new Date().toISOString() });
      await redis("SET", "reel:" + key, JSON.stringify(st));
    }

    // attendre la fin du traitement de la vidéo (≈ 50 s max par appel ; sinon rappeler la même adresse)
    let status = "";
    for (let i = 0; i < 12; i++) {
      const s2 = await graph("/" + st.container, { fields: "status_code,status", access_token: auth.pageToken });
      status = s2.status_code;
      if (status === "FINISHED") break;
      if (status === "ERROR" || status === "EXPIRED") { await redis("DEL", "reel:" + key); return send(502, { ok: false, error: "traitement Instagram : " + (s2.status || status) }); }
      await sleep(4000);
    }
    if (status !== "FINISHED") return send(202, { ok: false, pending: true, status, message: "vidéo encore en traitement : rappeler la même adresse dans une minute" });

    const pub = await graph(`/${auth.igId}/media_publish`, { creation_id: st.container, access_token: auth.pageToken }, "POST");
    let link = null; try { link = (await graph("/" + pub.id, { fields: "permalink", access_token: auth.pageToken })).permalink; } catch (e) {}
    let comment = null;
    if (c.comment) {   // premier commentaire (facultatif ; nécessite instagram_manage_comments, sinon simple avertissement)
      try { comment = { ok: true, id: (await graph(`/${pub.id}/comments`, { message: String(c.comment).slice(0, 2000), access_token: auth.pageToken }, "POST")).id }; }
      catch (e) { comment = { ok: false, error: String(e.message || e).slice(0, 200) }; }
    }
    Object.assign(st, { published: new Date().toISOString(), media: pub.id, link, comment });
    await redis("SET", "reel:" + key, JSON.stringify(st));
    return send(200, { ok: true, ...st });
  } catch (e) {
    return send(502, { ok: false, error: String(e.message || e).slice(0, 300), code: e.meta && e.meta.code });
  }
};
