/* Ciel vivant du bandeau : le décor suit l'heure (aube, jour, crépuscule, nuit) et le temps qu'il fait sur les pistes de Megève
   (en altitude, ~1 850 m, comme le mode « En altitude » de la page météo).
   Météo : Open-Meteo (sans clé), gardée 20 min dans le navigateur. Styles : assets/ciel.css.
   Chargé dans le <head> (sans defer) pour que le bon ciel s'affiche dès le premier rendu.
   Aperçu de toutes les combinaisons : ?ciel=aube|jour|crepuscule|nuit&meteo=clair|eclaircies|nuages|pluie|neige|brouillard|orage */
(function () {
  var LAT = 45.8567, LON = 6.6175, ALT = 1850, KEY = "mpc-ciel-v3", TTL = 20 * 60 * 1000;
  var root = document.documentElement;
  var q = new URLSearchParams(location.search);
  var CIELS = ["aube", "jour", "crepuscule", "nuit"], METEOS = ["clair", "eclaircies", "nuages", "pluie", "neige", "brouillard", "orage"];
  var forceC = CIELS.indexOf(q.get("ciel")) >= 0 ? q.get("ciel") : null;
  var forceM = METEOS.indexOf(q.get("meteo")) >= 0 ? q.get("meteo") : null;

  /* ---------- lever et coucher du soleil (calcul astronomique, en attendant Open-Meteo) ---------- */
  function sunTimes(d) {
    var rad = Math.PI / 180, start = Date.UTC(d.getUTCFullYear(), 0, 1);
    var n = Math.floor((d - start) / 864e5) + 1, g = 2 * Math.PI / 365 * (n - 1);
    var eq = 229.18 * (0.000075 + 0.001868 * Math.cos(g) - 0.032077 * Math.sin(g) - 0.014615 * Math.cos(2 * g) - 0.040849 * Math.sin(2 * g));
    var dec = 0.006918 - 0.399912 * Math.cos(g) + 0.070257 * Math.sin(g) - 0.006758 * Math.cos(2 * g) + 0.000907 * Math.sin(2 * g) - 0.002697 * Math.cos(3 * g) + 0.00148 * Math.sin(3 * g);
    var ha = Math.acos(Math.cos(90.833 * rad) / (Math.cos(LAT * rad) * Math.cos(dec)) - Math.tan(LAT * rad) * Math.tan(dec)) / rad;
    var day = Date.UTC(d.getUTCFullYear(), d.getUTCMonth(), d.getUTCDate());
    return { rise: day + (720 - 4 * (LON + ha) - eq) * 6e4, set: day + (720 - 4 * (LON - ha) - eq) * 6e4 };
  }
  function phase(now, rise, set) {
    var m = 6e4;
    if (now >= rise - 40 * m && now < rise + 35 * m) return "aube";
    if (now >= set - 35 * m && now < set + 40 * m) return "crepuscule";
    if (now >= rise + 35 * m && now < set - 35 * m) return "jour";
    return "nuit";
  }

  /* ---------- code météo WMO -> ambiance ---------- */
  function kind(c, snow, temp) {
    if (c >= 95) return "orage";
    if (c === 45 || c === 48) return "brouillard";
    if ((c >= 71 && c <= 77) || c === 85 || c === 86) return "neige";
    if ((c >= 51 && c <= 67) || (c >= 80 && c <= 82)) return (snow > 0 || (temp != null && temp <= 1.5)) ? "neige" : "pluie"; // à 1 850 m, sous ~1,5 °C c'est de la neige
    if (c === 3) return "nuages";
    if (c === 2) return "eclaircies";
    return "clair";
  }
  function force(c) { // intensité des précipitations
    if ([51, 53, 56, 61, 66, 71, 77, 80, 85].indexOf(c) >= 0) return .55;
    if ([55, 57, 65, 67, 75, 82, 86, 96, 99].indexOf(c) >= 0) return 1.6;
    return 1;
  }

  var state = { ciel: null, meteo: "clair", force: 1, vent: .3 };
  function read() { try { return JSON.parse(localStorage.getItem(KEY) || "null"); } catch (e) { return null; } }
  function save(o) { try { localStorage.setItem(KEY, JSON.stringify(o)); } catch (e) {} }

  function compute(data) {
    var now = Date.now(), st = sunTimes(new Date(now));
    var rise = st.rise, set = st.set;
    if (data && data.rise && new Date(data.rise).toDateString() === new Date(now).toDateString()) { rise = data.rise; set = data.set; }
    state.ciel = forceC || phase(now, rise, set);
    if (forceM) { state.meteo = forceM; state.force = 1; state.vent = .35; }
    else if (data && now - data.t < 3 * 3600e3) { state.meteo = kind(data.code, data.snow, data.temp); state.force = force(data.code); state.vent = Math.min(1, (data.wind || 0) / 40); }
    else state.meteo = "clair";
    root.setAttribute("data-ciel", state.ciel);
    root.setAttribute("data-meteo", state.meteo);
  }

  var cache = read();
  compute(cache); // tout de suite, avant le premier rendu

  function fetchMeteo() {
    if (forceC && forceM) return;
    var c = read();
    if (c && Date.now() - c.t < TTL) return;
    var url = "https://api.open-meteo.com/v1/forecast?latitude=" + LAT + "&longitude=" + LON + "&elevation=" + ALT +
      "&current=weather_code,snowfall,temperature_2m,wind_speed_10m&daily=sunrise,sunset&timezone=UTC&timeformat=unixtime&forecast_days=1";
    // Open-Meteo en direct, sinon relais du site /api/meteo (quota de l'adresse épuisé, panne…)
    fetch(url).then(function (r) { if (!r.ok) throw r.status; return r.json(); })
      .catch(function () { return fetch(url.replace("https://api.open-meteo.com/v1/forecast", "/api/meteo")).then(function (r) { return r.json(); }); })
      .then(function (j) {
      if (!j || !j.current) return;
      var o = { t: Date.now(), code: j.current.weather_code, snow: j.current.snowfall || 0, temp: j.current.temperature_2m, wind: j.current.wind_speed_10m || 0,
        rise: j.daily && j.daily.sunrise ? j.daily.sunrise[0] * 1000 : 0, set: j.daily && j.daily.sunset ? j.daily.sunset[0] * 1000 : 0 };
      save(o); var before = state.meteo + state.ciel; compute(o);
      if (before !== state.meteo + state.ciel) precip.reset();
    }).catch(function () {});
  }

  /* ---------- décor : couches ajoutées au bandeau ---------- */
  var precip = { reset: function () {} };
  function build() {
    var hero = document.querySelector(".hero");
    if (!hero || hero.querySelector(".ciel")) return;
    var rm = matchMedia("(prefers-reduced-motion: reduce)").matches;
    var sky = document.createElement("div");
    sky.className = "ciel"; sky.setAttribute("aria-hidden", "true");
    var clouds = "";
    for (var i = 0; i < 8; i++) {
      var w = 120 + Math.random() * 170, d = 70 + Math.random() * 80;
      clouds += '<i style="--y:' + (4 + Math.random() * 30).toFixed(1) + '%;--w:' + w.toFixed(0) + 'px;--o:' + (.45 + Math.random() * .4).toFixed(2) +
        ';--d:' + d.toFixed(0) + 's;--dl:-' + (Math.random() * d).toFixed(0) + 's;--x:' + (Math.random() * 90).toFixed(0) + 'vw"></i>';
    }
    sky.innerHTML = '<div class="ciel-etoiles"></div><div class="ciel-brume"></div><div class="ciel-astre"><i class="soleil"></i><i class="lune"></i></div>' +
      '<div class="ciel-nuages">' + clouds + '</div><div class="ciel-eclair"></div>';
    hero.insertBefore(sky, hero.firstChild);
    var front = document.createElement("div"); front.className = "ciel-brume-avant"; front.setAttribute("aria-hidden", "true");
    hero.appendChild(front);
    var cv = document.createElement("canvas"); cv.className = "ciel-precip"; cv.setAttribute("aria-hidden", "true");
    hero.appendChild(cv);

    /* pluie et neige */
    var x = cv.getContext("2d"), W = 0, H = 0, P = [], t = 0, raf = 0, visible = true, mode = "";
    function size() { var r = cv.getBoundingClientRect(); W = cv.width = r.width; H = cv.height = r.height; }
    function seed() {
      mode = state.meteo === "neige" ? "neige" : (state.meteo === "pluie" || state.meteo === "orage") ? "pluie" : "";
      P = [];
      if (!mode) return;
      var n = mode === "neige" ? Math.min(260, W * H / 5200) : Math.min(320, W * H / 3600);
      n = Math.round(n * state.force);
      for (var i = 0; i < n; i++) {
        var z = Math.random();
        P.push(mode === "neige"
          ? { x: Math.random() * W, y: Math.random() * H, z: z, r: .6 + z * z * 3.6, s: .25 + z * 1.25, d: Math.random() * 6.28, a: .35 + z * .6 }
          : { x: Math.random() * W, y: Math.random() * H, z: z, l: 9 + z * 12, s: 7 + z * 7, a: .18 + z * .4 });
      }
    }
    function draw() {
      x.clearRect(0, 0, W, H);
      if (mode === "neige") {
        var wind = (Math.sin(t) * .35 + .15) * (.6 + state.vent);
        x.fillStyle = "#fff";
        for (var i = 0; i < P.length; i++) {
          var p = P[i];
          if (!rm) { p.y += p.s; p.d += .012 + p.z * .01; p.x += Math.sin(p.d) * .35 * p.z + wind * p.z;
            if (p.y > H + 6) { p.y = -6; p.x = Math.random() * W; } if (p.x > W + 6) p.x = -6; if (p.x < -6) p.x = W + 6; }
          x.globalAlpha = p.a;
          if (p.r > 2.6) { x.shadowColor = "rgba(255,255,255,.9)"; x.shadowBlur = 6; } else x.shadowBlur = 0;
          x.beginPath(); x.arc(p.x, p.y, p.r, 0, 6.283); x.fill();
        }
        x.shadowBlur = 0;
      } else if (mode === "pluie") {
        var slant = .12 + state.vent * .35;
        x.strokeStyle = state.ciel === "jour" ? "#e4edf7" : "#b9cbe0"; x.lineCap = "round";
        for (var k = 0; k < P.length; k++) {
          var q = P[k];
          if (!rm) { q.y += q.s; q.x += q.s * slant; if (q.y > H + 20) { q.y = -20; q.x = Math.random() * (W + 100) - 100; } if (q.x > W + 20) q.x = -20; }
          x.globalAlpha = q.a; x.lineWidth = .8 + q.z * .9;
          x.beginPath(); x.moveTo(q.x, q.y); x.lineTo(q.x - q.l * slant, q.y - q.l); x.stroke();
        }
      }
      x.globalAlpha = 1;
    }
    function loop() { t += .004; draw(); raf = (mode && visible && !rm) ? requestAnimationFrame(loop) : 0; }
    function start() { if (!raf) raf = requestAnimationFrame(loop); }
    precip.reset = function () { seed(); if (rm) draw(); else start(); if (!mode) x.clearRect(0, 0, W, H); };
    size(); precip.reset();
    addEventListener("resize", function () { size(); precip.reset(); });
    if ("IntersectionObserver" in window) new IntersectionObserver(function (e) { visible = e[0].isIntersecting; if (visible) start(); }).observe(hero);
    // l'heure tourne : on revérifie le ciel toutes les 5 minutes
    setInterval(function () { var b = state.ciel + state.meteo; compute(read()); fetchMeteo(); if (b !== state.ciel + state.meteo) precip.reset(); }, 5 * 60 * 1000);
  }

  if (document.readyState === "loading") document.addEventListener("DOMContentLoaded", build); else build();
  fetchMeteo();
})();
