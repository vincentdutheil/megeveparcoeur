// Cron Vercel : envoie les notifications « we » (voir api/push.js).
const push = require("./push.js");
module.exports = (req, res) => { req.url = "/api/push?job=we"; return push(req, res); };
