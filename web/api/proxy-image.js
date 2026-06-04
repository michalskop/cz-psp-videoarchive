// Vercel Platform Function: proxies external images server-side to avoid
// CORS restrictions when html2canvas captures cards with remote screenshots.
module.exports = async function handler(req, res) {
  const { url } = req.query;
  if (!url || typeof url !== "string") {
    return res.status(400).send("missing url");
  }

  let parsed;
  try { parsed = new URL(url); } catch {
    return res.status(400).send("invalid url");
  }
  if (parsed.protocol !== "http:" && parsed.protocol !== "https:") {
    return res.status(400).send("invalid protocol");
  }

  try {
    const upstream = await fetch(url, {
      headers: { "User-Agent": "Mozilla/5.0" },
    });
    const ct = upstream.headers.get("content-type") ?? "image/jpeg";
    if (!ct.startsWith("image/")) {
      return res.status(400).send("not an image");
    }
    const buf = await upstream.arrayBuffer();
    res.setHeader("Content-Type", ct);
    res.setHeader("Cache-Control", "public, max-age=86400, s-maxage=86400");
    res.setHeader("Access-Control-Allow-Origin", "*");
    return res.status(200).send(Buffer.from(buf));
  } catch {
    return res.status(502).send("upstream error");
  }
};
