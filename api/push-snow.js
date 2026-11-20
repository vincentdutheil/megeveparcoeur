// Cron Vercel : envoie les notifications « snow » (voir api/push.js).
const push = require("./push.js");
module.exports = (req, res) => { req.url = "/api/push?job=snow"; return push(req, res); };
