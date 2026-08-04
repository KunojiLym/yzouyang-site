/**
 * DIY first-party pageview beacon (supplement to Jetpack / optional GA4).
 * No cookies. Honors DNT when configured. Payload is path/referrer/viewport only.
 */
(function () {
  var script = document.currentScript;
  if (!script) return;

  var collectUrl = (script.getAttribute("data-collect-url") || "").trim();
  if (!collectUrl) return;

  var honorDnt = script.getAttribute("data-honor-dnt") !== "false";
  if (honorDnt && (navigator.doNotTrack === "1" || window.doNotTrack === "1")) {
    return;
  }

  function payload() {
    var ref = document.referrer || "";
    var refHost = "";
    try {
      if (ref) refHost = new URL(ref).hostname;
    } catch (e) {
      refHost = "";
    }
    return {
      t: "pageview",
      v: 1,
      ts: new Date().toISOString(),
      path: location.pathname + location.search,
      host: location.hostname,
      title: document.title || "",
      ref: refHost,
      lang: (navigator.language || "").slice(0, 16),
      tz: Intl.DateTimeFormat().resolvedOptions().timeZone || "",
      vw: Math.min(window.innerWidth || 0, 10000),
      vh: Math.min(window.innerHeight || 0, 10000),
    };
  }

  function send() {
    var body = JSON.stringify(payload());
    try {
      if (navigator.sendBeacon) {
        var blob = new Blob([body], { type: "application/json" });
        if (navigator.sendBeacon(collectUrl, blob)) return;
      }
    } catch (e) {
      /* fall through */
    }
    try {
      fetch(collectUrl, {
        method: "POST",
        headers: { "content-type": "application/json" },
        body: body,
        mode: "cors",
        keepalive: true,
        credentials: "omit",
      }).catch(function () {});
    } catch (e) {
      /* ignore */
    }
  }

  if (document.readyState === "complete") {
    send();
  } else {
    window.addEventListener("load", send, { once: true });
  }
})();
