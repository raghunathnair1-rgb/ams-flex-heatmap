import React, { useMemo, useState } from "react";

// Sequential single-hue scale: light = cheap, dark = expensive.
// Stops chosen for perceptual smoothness and readable text contrast at both ends.
const SCALE = ["#eaf2ff", "#c3d9fb", "#8fb8f6", "#5a92e8", "#2f68c9", "#173f8a"];

function colorFor(t) {
  const idx = Math.min(SCALE.length - 2, Math.floor(t * (SCALE.length - 1)));
  return SCALE[idx];
}

function textColorFor(t) {
  return t > 0.55 ? "#f5f8ff" : "#12203f";
}

const WEEKDAY_LABELS = ["Mon", "Tue", "Wed", "Thu", "Fri", "Sat", "Sun"];

function compareLinks(origin, destIata, date) {
  const yymmdd = date.replace(/-/g, "").slice(2);
  return {
    skyscanner: `https://www.skyscanner.net/transport/flights/${origin.toLowerCase()}/${(destIata || "").toLowerCase()}/${yymmdd}/`,
    googleFlights: `https://www.google.com/travel/flights?q=${encodeURIComponent(
      `flights from ${origin} to ${destIata || ""} on ${date}`
    )}`,
  };
}

export default function Heatmap({ data }) {
  const [hovered, setHovered] = useState(null);

  const { weeks, min, max, cheapest } = useMemo(() => {
    if (!data?.days?.length) return { weeks: [], min: 0, max: 0, cheapest: null };
    const days = data.days;
    const prices = days.map((d) => d.price);
    const min = Math.min(...prices);
    const max = Math.max(...prices);

    // Pad the first week so it starts on Monday, for a real calendar grid.
    const first = new Date(days[0].date);
    const leadingBlanks = (first.getDay() + 6) % 7;
    const cells = [...Array(leadingBlanks).fill(null), ...days];
    const weeks = [];
    for (let i = 0; i < cells.length; i += 7) weeks.push(cells.slice(i, i + 7));

    const cheapest = days.reduce((a, b) => (b.price < a.price ? b : a));
    return { weeks, min, max, cheapest };
  }, [data]);

  if (!data?.days?.length) return null;

  const isMock = (data.source || "").startsWith("mock");
  const links = compareLinks(data.origin, data.destination_iata, cheapest.date);

  return (
    <div className="heatmap">
      <div className={`data-source-badge ${isMock ? "mock" : "real"}`}>
        {isMock ? "⚠ Mock data" : "✓ Live Amadeus data"} &middot; {data.source}
      </div>

      <div className="heatmap-header">
        <div>
          <div className="heatmap-title">
            AMS &rarr; {data.destination} &middot; flex-date prices
          </div>
          <div className="heatmap-subtitle">
            Cheapest: <strong>€{cheapest.price}</strong> on{" "}
            {new Date(cheapest.date).toLocaleDateString(undefined, {
              weekday: "long",
              month: "short",
              day: "numeric",
            })}
            {cheapest.airline && <> ({cheapest.airline})</>}
          </div>
          <div className="compare-links">
            Compare:{" "}
            <a href={links.skyscanner} target="_blank" rel="noopener noreferrer">
              Skyscanner
            </a>{" "}
            &middot;{" "}
            <a href={links.googleFlights} target="_blank" rel="noopener noreferrer">
              Google Flights
            </a>
          </div>
        </div>
        <Legend min={min} max={max} />
      </div>

      <div className="heatmap-grid">
        {WEEKDAY_LABELS.map((w) => (
          <div key={w} className="heatmap-weekday">
            {w}
          </div>
        ))}
        {weeks.map((week, wi) =>
          week.map((day, di) => {
            if (!day) return <div key={`${wi}-${di}`} className="heatmap-cell empty" />;
            const t = max === min ? 0.5 : (day.price - min) / (max - min);
            const bg = colorFor(t);
            const fg = textColorFor(t);
            const isCheapest = day.date === cheapest.date;
            return (
              <div
                key={day.date}
                className={`heatmap-cell${isCheapest ? " cheapest" : ""}`}
                style={{ background: bg, color: fg }}
                onMouseEnter={() => setHovered(day)}
                onMouseLeave={() => setHovered(null)}
                tabIndex={0}
                aria-label={`${day.date}: €${day.price}${day.airline ? `, ${day.airline}` : ""}`}
              >
                <span className="heatmap-daynum">{new Date(day.date).getDate()}</span>
                <span className="heatmap-price">€{Math.round(day.price)}</span>
                {isCheapest && <span className="heatmap-badge">best</span>}
              </div>
            );
          })
        )}
      </div>

      {hovered && (
        <div className="heatmap-tooltip">
          <strong>{new Date(hovered.date).toDateString()}</strong> &middot; €{hovered.price}
          {hovered.airline && <> &middot; {hovered.airline}</>}
          {hovered.stops !== undefined && (
            <> &middot; {hovered.stops === 0 ? "direct" : `${hovered.stops} stop`}</>
          )}
          {hovered.duration_min !== undefined && (
            <>
              {" "}
              &middot; {Math.round(hovered.duration_min / 60)}h {hovered.duration_min % 60}m
            </>
          )}
          {!hovered.airline && (
            <span className="tooltip-hint"> &middot; full details shown for cheapest day only</span>
          )}
        </div>
      )}
    </div>
  );
}

function Legend({ min, max }) {
  return (
    <div className="legend">
      <span className="legend-label">€{Math.round(min)}</span>
      <div className="legend-bar">
        {SCALE.map((c, i) => (
          <span key={i} style={{ background: c }} />
        ))}
      </div>
      <span className="legend-label">€{Math.round(max)}</span>
    </div>
  );
}
