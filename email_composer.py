from collections import Counter
from datetime import date


PERIODS = [
    ("Morning",   6,  12),
    ("Afternoon", 12, 17),
    ("Evening",   17, 21),
    ("Night",     21, 30),  # 30 wraps to cover midnight hours stored as 21–23
]


def _hours_in_period(hours, start, end):
    return [h for h in hours if start <= h["hour"] < min(end, 24)]


def _dominant_condition(period_hours):
    if not period_hours:
        return "Unknown"
    counts = Counter(h["condition"] for h in period_hours)
    return counts.most_common(1)[0][0]


def _peak_precip_hour(period_hours):
    if not period_hours:
        return None
    peak = max(period_hours, key=lambda h: h["precipitation"])
    if peak["precipitation"] == 0:
        return None
    return peak


def _precip_type(period_hours):
    total_snow = sum(h["snowfall"] for h in period_hours)
    total_rain = sum(h["rain"] for h in period_hours)
    if total_snow > 0 and total_rain > 0:
        return "mixed rain and snow"
    if total_snow > 0:
        return "snow"
    if total_rain > 0:
        return "rain"
    return None


def _summarize_period(name, period_hours):
    if not period_hours:
        return None

    temps = [h["temp"] for h in period_hours]
    feels = [h["feels_like"] for h in period_hours]
    humidities = [h["humidity"] for h in period_hours]
    total_precip = sum(h["precipitation"] for h in period_hours)
    condition = _dominant_condition(period_hours)
    peak = _peak_precip_hour(period_hours)
    ptype = _precip_type(period_hours)
    winds = [h["windspeed"] for h in period_hours]

    summary = {
        "name": name,
        "condition": condition,
        "temp_low": round(min(temps)),
        "temp_high": round(max(temps)),
        "feels_like_avg": round(sum(feels) / len(feels)),
        "humidity_avg": round(sum(humidities) / len(humidities)),
        "total_precip": round(total_precip, 2),
        "precip_type": ptype,
        "peak_precip_hour": peak,
        "wind_avg": round(sum(winds) / len(winds)),
        "wind_max": round(max(winds)),
    }
    return summary


def _narrative_sentence(summary, prev_condition=None):
    name = summary["name"]
    cond = summary["condition"]
    lo = summary["temp_low"]
    hi = summary["temp_high"]
    feels = summary["feels_like_avg"]
    hum = summary["humidity_avg"]
    precip = summary["total_precip"]
    ptype = summary["precip_type"]
    peak = summary["peak_precip_hour"]
    wind = summary["wind_avg"]
    wind_max = summary["wind_max"]

    # Transition phrase
    if prev_condition and prev_condition != cond:
        transition = f"{cond.lower()} moving in for the"
    else:
        transition = cond

    parts = [f"<b>{name}:</b> {transition}, {lo}–{hi}°F (feels like {feels}°F), {hum}% humidity"]

    if precip > 0 and ptype:
        precip_detail = f"{precip:.2f} in. of {ptype}"
        if peak:
            hour = peak["hour"]
            ampm = "AM" if hour < 12 else "PM"
            display_hour = hour if hour <= 12 else hour - 12
            display_hour = 12 if display_hour == 0 else display_hour
            precip_detail += f" (heaviest around {display_hour} {ampm})"
        parts.append(precip_detail)

    if wind_max >= 25:
        parts.append(f"gusty winds up to {wind_max} mph")
    elif wind >= 15:
        parts.append(f"breezy at {wind} mph avg")

    return ", ".join(parts) + "."


def compose_email(hours):
    today = date.today().strftime("%A, %B %-d, %Y")

    period_summaries = []
    for name, start, end in PERIODS:
        period_hours = _hours_in_period(hours, start, end)
        s = _summarize_period(name, period_hours)
        if s:
            period_summaries.append(s)

    # Overall day stats
    all_temps = [h["temp"] for h in hours]
    all_precip = sum(h["precipitation"] for h in hours)
    day_lo = round(min(all_temps))
    day_hi = round(max(all_temps))

    subject = f"NYC Weather for {today} — {day_lo}–{day_hi}°F"
    if all_precip > 0:
        ptype = _precip_type(hours)
        subject += f", {all_precip:.2f}\" {ptype or 'precip'}"

    # Plain text
    lines = [f"NYC Weather Forecast — {today}", "=" * 50, ""]
    prev_cond = None
    for s in period_summaries:
        line = _narrative_sentence(s, prev_cond)
        # Strip HTML tags for plain text
        line = line.replace("<b>", "").replace("</b>", "")
        lines.append(line)
        prev_cond = s["condition"]

    lines += ["", f"Daily range: {day_lo}–{day_hi}°F"]
    if all_precip > 0:
        lines.append(f"Total precipitation: {all_precip:.2f} inches")
    lines += ["", "—", "Powered by Open-Meteo (open-meteo.com)"]
    plain_text = "\n".join(lines)

    # HTML
    html_parts = [
        "<!DOCTYPE html><html><body style='font-family:sans-serif;max-width:600px;margin:auto;padding:20px'>",
        f"<h2 style='color:#1a73e8'>NYC Weather — {today}</h2>",
        f"<p style='font-size:1.1em;color:#333'>Daily range: <strong>{day_lo}–{day_hi}°F</strong>",
    ]
    if all_precip > 0:
        ptype = _precip_type(hours)
        html_parts.append(f" &nbsp;|&nbsp; Total precipitation: <strong>{all_precip:.2f}\"</strong> {ptype or ''}")
    html_parts.append("</p><hr>")

    prev_cond = None
    for s in period_summaries:
        sentence = _narrative_sentence(s, prev_cond)
        html_parts.append(f"<p style='margin:12px 0'>{sentence}</p>")
        prev_cond = s["condition"]

    html_parts += [
        "<hr>",
        "<p style='color:#888;font-size:0.8em'>Powered by <a href='https://open-meteo.com'>Open-Meteo</a></p>",
        "</body></html>",
    ]
    html = "\n".join(html_parts)

    return subject, plain_text, html
