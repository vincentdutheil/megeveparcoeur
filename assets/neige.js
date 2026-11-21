// « La neige cette semaine » : neige au sol + chutes prévues sur 7 jours (données /api/neige, Open-Meteo).
// - #snowbox (accueil) : encart compact, nos 4 villages
// - #classement (page météo) : classement des stations du coin, nos 4 villages en rouge
(function () {
  const box = document.getElementById("snowbox"), cl = document.getElementById("classement");
  if (!box && !cl) return;
  const EN = document.documentElement.lang === "en";
  const T = EN
    ? { t: "Snow this week", more: "Full forecast →", sol: "on the ground", prev: "next 7 days", hs: "On the ground", hp: "Next 7 days",
        h2: "Snow this week, resort by resort", lead: (a, b) => `Estimated snow on the ground today and total snowfall expected from ${a} to ${b}, at ski-area altitude. Our four villages are in red.`,
        src: "Model estimates (Open-Meteo), updated several times a day; they may differ from the depths measured on the pistes.", meteo: "/en/meteo/#neige", loc: "en-GB" }
    : { t: "La neige cette semaine", more: "Tout le détail →", sol: "au sol", prev: "prévus sur 7 j", hs: "Au sol", hp: "Prévu 7 j",
        h2: "La neige cette semaine, station par station", lead: (a, b) => `Neige au sol estimée aujourd'hui et cumul des chutes prévues du ${a} au ${b}, à l'altitude des domaines. Nos quatre villages sont en rouge.`,
        src: "Estimations des modèles (Open-Meteo), mises à jour plusieurs fois par jour ; elles peuvent différer des hauteurs mesurées sur les pistes.", meteo: "/meteo/#neige", loc: "fr-FR" };
  const HOME = ["Megève", "Combloux", "Demi-Quartier", "Praz-sur-Arly"];
  const css = `
#snowbox{max-width:780px;margin:0 auto 14px}
.snb{display:block;background:linear-gradient(135deg,#0e2142,#1f4f9a);color:#fff;border-radius:18px;padding:14px 16px 16px;text-decoration:none;box-shadow:0 10px 30px rgba(18,40,74,.18)}
.snb-h{display:flex;justify-content:space-between;align-items:baseline;gap:10px;margin-bottom:10px}
.snb-h b{font-size:1.05rem}.snb-h span{font-size:.85rem;font-weight:800;color:#bcd3f2;white-space:nowrap}
.snb-g{display:grid;grid-template-columns:repeat(4,1fr);gap:8px}
.snb-c{background:rgba(255,255,255,.1);border:1px solid rgba(255,255,255,.16);border-radius:12px;padding:8px 10px}
.snb-c .n{font-weight:800;font-size:.9rem;white-space:nowrap;overflow:hidden;text-overflow:ellipsis}
.snb-c .p{font-size:1.35rem;font-weight:800;line-height:1.15;margin-top:2px}.snb-c .p small{font-size:.7rem;font-weight:700;color:#bcd3f2;display:block}
.snb-c .s{font-size:.78rem;color:#d8e5f7;margin-top:3px}
@media(max-width:560px){.snb-g{grid-template-columns:repeat(2,1fr)}}
.cls{margin:34px 0 10px}.cls h2{font-family:var(--display);font-size:clamp(1.5rem,3.2vw,2rem);margin:0 0 6px}.cls .lead{color:var(--muted);margin:0 0 14px}
.cls-t{display:flex;flex-direction:column;gap:7px;max-width:760px}
.cls-r,.cls-hd{display:grid;grid-template-columns:1fr 110px 110px;gap:8px;align-items:center}
.cls-hd{font-size:.72rem;font-weight:800;text-transform:uppercase;letter-spacing:.06em;color:var(--muted);padding:0 8px 0 16px}.cls-hd span{text-align:center}
.cls-r{background:var(--card);border:1px solid var(--line);border-radius:14px;padding:7px 8px 7px 16px;font-weight:800}
.cls-r .k{opacity:.55;font-weight:700;margin-right:4px}.cls-r .nm{white-space:nowrap;overflow:hidden;text-overflow:ellipsis}
.cls-r i,.cls-r b{text-align:center;border-radius:10px;padding:5px 0;font-style:normal}
.cls-r i{background:var(--wool);color:var(--muted)}.cls-r b{background:#1f4f9a;color:#fff}
.cls-r.home{background:#c8323d;border-color:#c8323d;color:#fff}.cls-r.home i{background:rgba(255,255,255,.2);color:#fff}.cls-r.home b{background:#fff;color:#c8323d}
.cls .src{font-size:.85rem;color:var(--muted);margin-top:10px}
@media(max-width:560px){.cls-r,.cls-hd{grid-template-columns:1fr 78px 84px}.cls-r{font-size:.92rem}}`;
  const st = document.createElement("style"); st.textContent = css; document.head.appendChild(st);
  const d = s => new Date(s + "T12:00:00").toLocaleDateString(T.loc, { day: "numeric", month: "long" });
  fetch("/api/neige").then(r => r.json()).then(j => {
    if (!j.stations) return;
    if (box) {
      const v = HOME.map(n => j.stations.find(s => s.nom === n)).filter(Boolean);
      box.innerHTML = `<a class="snb" href="${T.meteo}"><div class="snb-h"><b>❄️ ${T.t}</b><span>${T.more}</span></div><div class="snb-g">${
        v.map(s => `<div class="snb-c"><div class="n">${s.nom}</div><div class="p">+${s.prevu} cm<small>${T.prev}</small></div><div class="s">${s.sol} cm ${T.sol}</div></div>`).join("")}</div></a>`;
      box.hidden = false;
    }
    if (cl) {
      cl.innerHTML = `<h2>❄️ ${T.h2}</h2><p class="lead">${T.lead(d(j.du), d(j.au))}</p><div class="cls-t"><div class="cls-hd"><span></span><span>${T.hs}</span><span>${T.hp}</span></div>${
        j.stations.map((s, i) => `<div class="cls-r${HOME.includes(s.nom) ? " home" : ""}"><span class="nm"><span class="k">${i + 1}.</span>${s.nom}</span><i>${s.sol} cm</i><b>+${s.prevu} cm</b></div>`).join("")
      }</div><p class="src">${T.src}</p>`;
      cl.hidden = false;
    }
  }).catch(() => {});
})();
