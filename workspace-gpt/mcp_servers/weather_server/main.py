"""Weather MCP server using the public wttr.in JSON endpoint."""

from __future__ import annotations

from typing import Any

import httpx
from mcp.server.fastmcp import FastMCP

mcp = FastMCP("weather")


@mcp.tool()
def current_weather(location: str) -> dict[str, Any]:
    """Return current weather for a location."""
    url = f"https://wttr.in/{location}"
    with httpx.Client(timeout=20.0) as client:
        response = client.get(url, params={"format": "j1"})
        response.raise_for_status()
        data = response.json()
    current = data["current_condition"][0]
    area = data.get("nearest_area", [{}])[0]
    return {
        "location": area.get("areaName", [{"value": location}])[0]["value"],
        "country": area.get("country", [{"value": ""}])[0]["value"],
        "temperature_c": current.get("temp_C"),
        "feels_like_c": current.get("FeelsLikeC"),
        "humidity": current.get("humidity"),
        "description": current.get("weatherDesc", [{"value": ""}])[0]["value"],
        "wind_kmph": current.get("windspeedKmph"),
    }


@mcp.tool()
def weather_forecast(location: str, days: int = 3) -> list[dict[str, Any]]:
    """Return a compact weather forecast."""
    url = f"https://wttr.in/{location}"
    with httpx.Client(timeout=20.0) as client:
        response = client.get(url, params={"format": "j1"})
        response.raise_for_status()
        data = response.json()
    return [
        {
            "date": day["date"],
            "avg_temp_c": day["avgtempC"],
            "max_temp_c": day["maxtempC"],
            "min_temp_c": day["mintempC"],
            "sunrise": day["astronomy"][0]["sunrise"],
            "sunset": day["astronomy"][0]["sunset"],
        }
        for day in data.get("weather", [])[:days]
    ]


if __name__ == "__main__":
    mcp.run()
