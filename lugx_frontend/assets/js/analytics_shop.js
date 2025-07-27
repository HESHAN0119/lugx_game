// // static/js/analytics.js
// (function () {
//   sendAnalyticsEvent({
//     eventType: "page_view",
//     url: window.location.href,
//     timestamp: Date.now(),
//   });

//   document.addEventListener("click", (e) => {
//     sendAnalyticsEvent({
//       eventType: "click",
//       element: e.target.tagName,
//       text: e.target.textContent?.trim().slice(0, 100),
//       url: window.location.href,
//       timestamp: Date.now(),
//     });
//   });

//   window.addEventListener("scroll", () => {
//     const scrollPercent = Math.round(
//       ((window.scrollY + window.innerHeight) / document.body.scrollHeight) * 100
//     );
//     sendAnalyticsEvent({
//       eventType: "scroll",
//       scrollPercent,
//       url: window.location.href,
//       timestamp: Date.now(),
//     });
//   });

//   let startTime = Date.now();
//   window.addEventListener("beforeunload", () => {
//     const duration = Date.now() - startTime;
//     sendAnalyticsEvent({
//       eventType: "page_time",
//       durationMs: duration,
//       url: window.location.href,
//       timestamp: Date.now(),
//     });
//   });

//   function sendAnalyticsEvent(data) {
//     navigator.sendBeacon(
//       "http://localhost:8000/api/analytics",
//       JSON.stringify(data)
//     );
//   }
// })();
// (function () {
//   // Send page view event on load
//   sendAnalyticsEvent({
//     event_type: "page_view",
//     url: window.location.href,
//     timestamp: new Date().toISOString(),
//   });

//   // Click event listener
//   document.addEventListener("click", (e) => {
//     sendAnalyticsEvent({
//       event_type: "click",
//       element: e.target.tagName,
//       text: (e.target.textContent || "").trim().slice(0, 100),
//       url: window.location.href,
//       timestamp: new Date().toISOString(),
//     });
//   });

//   // Scroll event listener
//   window.addEventListener("scroll", () => {
//     const scroll_percent = Math.round(
//       ((window.scrollY + window.innerHeight) / document.body.scrollHeight) * 100
//     );
//     sendAnalyticsEvent({
//       event_type: "scroll",
//       scroll_percent: scroll_percent,
//       url: window.location.href,
//       timestamp: new Date().toISOString(),
//     });
//   });

//   // Page time event listener
//   let startTime = Date.now();
//   window.addEventListener("beforeunload", () => {
//     const duration_ms = Date.now() - startTime;
//     sendAnalyticsEvent({
//       event_type: "page_time",
//       duration_ms: duration_ms,
//       url: window.location.href,
//       timestamp: new Date().toISOString(),
//     });
//   });

//   // Function to send analytics data
//   function sendAnalyticsEvent(data) {
//     fetch("http://localhost:8000/api/analytics", {
//       method: "POST",
//       headers: {
//         "Content-Type": "application/json",
//       },
//       body: JSON.stringify(data),
//       keepalive: true,
//     })
//       .then((response) => {
//         if (!response.ok) {
//           console.error("Analytics request failed:", response.statusText);
//         }
//       })
//       .catch((error) => console.error("Error sending analytics:", error));
//   }
// })();

// (function () {
//   let startTime = Date.now();
//   let clickCount = 0;
//   let clickedItems = [];
//   let maxScrollPercent = 0;

//   // Click event listener
//   document.addEventListener("click", (e) => {
//     clickCount++;
//     clickedItems.push({
//       tag: e.target.tagName,
//       text: (e.target.textContent || "").trim().slice(0, 100),
//     });
//   });

//   // Scroll event listener
//   window.addEventListener("scroll", () => {
//     const scrollPercent = Math.round(
//       ((window.scrollY + window.innerHeight) / document.body.scrollHeight) * 100
//     );
//     if (scrollPercent > maxScrollPercent) {
//       maxScrollPercent = scrollPercent;
//     }
//   });

//   // Before unload: send all collected analytics
//   window.addEventListener("beforeunload", () => {
//     const durationMs = Date.now() - startTime;

//     const payload = {
//       event_type: "page_summary",
//       url: window.location.href,
//       total_time_ms: durationMs,
//       total_clicks: clickCount,
//       clicked_items: clickedItems,
//       max_scroll_percent: maxScrollPercent,
//       timestamp: new Date().toISOString(),
//     };

//     sendAnalyticsEvent(payload);
//   });

//   // Function to send analytics data
//   function sendAnalyticsEvent(data) {
//     navigator.sendBeacon(
//       "http://localhost:8000/api/analytics",
//       JSON.stringify(data)
//     );
//   }
// })();


(function () {
    console.log("Analytics script for shop loaded");
    let startTime = Date.now();
    let clickCount = 0;
    let clickedItems = [];
    let maxScrollPercent = 0;

    document.addEventListener("click", (e) => {
        console.log("Click event captured:", e.target.tagName);
        clickCount++;
        clickedItems.push({
            tag: e.target.tagName,
            text: (e.target.textContent || "").trim().slice(0, 100),
        });
    });

    window.addEventListener("scroll", () => {
        const scrollPercent = Math.round(
            ((window.scrollY + window.innerHeight) / document.body.scrollHeight) * 100
        );
        if (scrollPercent > maxScrollPercent) {
            maxScrollPercent = scrollPercent;
            console.log("Scroll percent updated:", maxScrollPercent);
        }
    });

    window.addEventListener("beforeunload", () => {
        console.log("Beforeunload event triggered");
        const durationMs = Date.now() - startTime;
        const payload = {
            event_type: "page_summary",
            url: window.location.href,
            total_time_ms: durationMs,
            total_clicks: clickCount,
            clicked_items: clickedItems,
            max_scroll_percent: maxScrollPercent,
            timestamp: new Date().toISOString(),
        };
        console.log("Sending payload:", payload);
        sendAnalyticsEvent(payload);
    });

    function sendAnalyticsEvent(data) {
        console.log("Sending analytics data to backend");
        fetch("http://52.190.8.54:8000/api/analytics/shop", {
            method: "POST",
            headers: { "Content-Type": "application/json" },
            body: JSON.stringify(data),
            keepalive: true
        })
        .then(response => {
            if (!response.ok) {
                console.error("Analytics request failed:", response.statusText);
            } else {
                console.log("Analytics data sent successfully");
            }
        })
        .catch(error => console.error("Error sending analytics:", error));
    }
})();