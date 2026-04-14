#!/usr/bin/env python3
"""
天气顾问 — 工具脚本
功能: now, outfit, alert

用法:
    python weather_advisor_tool.py now --city Beijing    # 查看天气
    python weather_advisor_tool.py outfit --city Beijing # 穿衣建议
    python weather_advisor_tool.py alert --city Beijing  # 天气预警
"""

import sys
import json
import os
import requests
from datetime import datetime

# Open-Meteo API (免费，无需API Key)
GEOCODING_API = "https://geocoding-api.open-meteo.com/v1/search"
WEATHER_API = "https://api.open-meteo.com/v1/forecast"

# 城市坐标缓存
CITY_CACHE = {}


def get_city_coords(city_name):
    """获取城市经纬度"""
    if city_name in CITY_CACHE:
        return CITY_CACHE[city_name]
    
    try:
        params = {
            "name": city_name,
            "count": 1,
            "language": "zh",
            "format": "json"
        }
        response = requests.get(GEOCODING_API, params=params, timeout=10)
        response.raise_for_status()
        data = response.json()
        
        if data.get("results"):
            result = data["results"][0]
            coords = {
                "latitude": result["latitude"],
                "longitude": result["longitude"],
                "name": result["name"],
                "country": result.get("country", "")
            }
            CITY_CACHE[city_name] = coords
            return coords
        else:
            return None
    except Exception as e:
        print(f"错误: 无法获取城市坐标 - {e}", file=sys.stderr)
        return None


def get_weather_data(latitude, longitude):
    """获取天气数据"""
    try:
        params = {
            "latitude": latitude,
            "longitude": longitude,
            "current": ["temperature_2m", "relative_humidity_2m", "apparent_temperature",
                       "precipitation", "weather_code", "wind_speed_10m", "wind_direction_10m"],
            "daily": ["weather_code", "temperature_2m_max", "temperature_2m_min", 
                     "precipitation_probability_max"],
            "timezone": "auto",
            "forecast_days": 7
        }
        
        response = requests.get(WEATHER_API, params=params, timeout=10)
        response.raise_for_status()
        return response.json()
    except Exception as e:
        print(f"错误: 无法获取天气数据 - {e}", file=sys.stderr)
        return None


def parse_weather_code(code):
    """解析WMO天气代码"""
    weather_codes = {
        0: "晴朗", 1: "主要晴朗", 2: "多云", 3: "阴天",
        45: "雾", 48: "雾凇",
        51: "毛毛雨", 53: "中度毛毛雨", 55: "大毛毛雨",
        56: "冻毛毛雨", 57: "强冻毛毛雨",
        61: "小雨", 63: "中雨", 65: "大雨",
        66: "冻雨", 67: "强冻雨",
        71: "小雪", 73: "中雪", 75: "大雪", 77: "雪粒",
        80: "小阵雨", 81: "中阵雨", 82: "强阵雨",
        85: "小阵雪", 86: "大阵雪",
        95: "雷雨", 96: "雷阵雨带冰雹", 99: "强雷阵雨带冰雹"
    }
    return weather_codes.get(code, f"未知天气({code})")


def get_clothing_advice(temp, weather_code):
    """根据温度和天气给出穿衣建议"""
    advice = []
    
    # 温度建议
    if temp < 0:
        advice.append("❄️ 极寒：羽绒服、保暖内衣、帽子、手套、围巾")
    elif temp < 10:
        advice.append("🧥 寒冷：厚外套、毛衣、长裤")
    elif temp < 20:
        advice.append("👔 凉爽：夹克、长袖衬衫、薄外套")
    elif temp < 28:
        advice.append("👕 舒适：T恤、薄长袖、牛仔裤")
    else:
        advice.append("🩳 炎热：短袖、短裤、凉鞋")
    
    # 天气建议
    if weather_code in [51, 53, 55, 61, 63, 65]:  # 雨天
        advice.append("☂️ 有雨：携带雨伞或雨衣")
    elif weather_code in [71, 73, 75]:  # 雪天
        advice.append("⛄ 有雪：防滑鞋、保暖衣物")
    elif weather_code in [95, 96, 99]:  # 雷雨
        advice.append("⚡ 雷雨：避免户外活动，注意安全")
    
    return advice


def now(args):
    """查看当前天气"""
    # 解析参数
    city = "Beijing"  # 默认城市
    for i, arg in enumerate(args):
        if arg in ["--city", "-c"] and i + 1 < len(args):
            city = args[i + 1]
    
    # 获取城市坐标
    coords = get_city_coords(city)
    if not coords:
        return {
            "status": "error",
            "message": f"无法找到城市: {city}"
        }
    
    # 获取天气数据
    weather = get_weather_data(coords["latitude"], coords["longitude"])
    if not weather:
        return {
            "status": "error",
            "message": "无法获取天气数据"
        }
    
    current = weather.get("current", {})
    daily = weather.get("daily", {})
    
    # 构建结果
    result = {
        "status": "success",
        "city": f"{coords['name']}, {coords.get('country', '')}",
        "timestamp": datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
        "current": {
            "temperature": f"{current.get('temperature_2m', 'N/A')}°C",
            "feels_like": f"{current.get('apparent_temperature', 'N/A')}°C",
            "humidity": f"{current.get('relative_humidity_2m', 'N/A')}%",
            "wind_speed": f"{current.get('wind_speed_10m', 'N/A')} km/h",
            "weather": parse_weather_code(current.get('weather_code', -1)),
            "precipitation": f"{current.get('precipitation', 0)} mm"
        },
        "forecast": []
    }
    
    # 未来7天预报
    if daily:
        for i in range(min(7, len(daily.get('time', [])))):
            result["forecast"].append({
                "date": daily['time'][i],
                "max_temp": f"{daily['temperature_2m_max'][i]}°C",
                "min_temp": f"{daily['temperature_2m_min'][i]}°C",
                "weather": parse_weather_code(daily['weather_code'][i]),
                "precipitation_prob": f"{daily['precipitation_probability_max'][i]}%"
            })
    
    return result


def outfit(args):
    """穿衣建议"""
    # 先获取天气
    weather_result = now(args)
    
    if weather_result["status"] != "success":
        return weather_result
    
    current = weather_result["current"]
    temp = float(current["temperature"].replace("°C", ""))
    weather_code_str = current["weather"]
    
    # 解析天气代码
    code_map = {v: k for k, v in {
        0: "晴朗", 1: "主要晴朗", 2: "多云", 3: "阴天",
        45: "雾", 48: "雾凇",
        51: "毛毛雨", 53: "中度毛毛雨", 55: "大毛毛雨",
        61: "小雨", 63: "中雨", 65: "大雨",
        71: "小雪", 73: "中雪", 75: "大雪",
        95: "雷雨", 96: "雷阵雨带冰雹", 99: "强雷阵雨带冰雹"
    }.items()}
    weather_code = code_map.get(weather_code_str, 0)
    
    # 获取穿衣建议
    clothing_advice = get_clothing_advice(temp, weather_code)
    
    return {
        "status": "success",
        "city": weather_result["city"],
        "timestamp": weather_result["timestamp"],
        "weather": {
            "temperature": current["temperature"],
            "feels_like": current["feels_like"],
            "condition": current["weather"]
        },
        "clothing_advice": clothing_advice,
        "recommendation": "建议" + "，".join(clothing_advice)
    }


def alert(args):
    """天气预警"""
    # 先获取天气
    weather_result = now(args)
    
    if weather_result["status"] != "success":
        return weather_result
    
    alerts = []
    current = weather_result["current"]
    forecast = weather_result.get("forecast", [])
    
    # 检查当前天气
    weather_desc = current["weather"]
    if "雨" in weather_desc or "雪" in weather_desc or "雷" in weather_desc:
        alerts.append({
            "level": "warning",
            "type": "current",
            "message": f"当前天气: {weather_desc}，请注意出行安全"
        })
    
    # 检查未来预报
    for day in forecast[:3]:  # 只看前3天
        if "雨" in day["weather"] or "雪" in day["weather"]:
            alerts.append({
                "level": "info",
                "type": "forecast",
                "date": day["date"],
                "message": f"{day['date']} 预计{day['weather']}，降水概率{day['precipitation_prob']}"
            })
    
    if not alerts:
        alerts.append({
            "level": "good",
            "type": "general",
            "message": "近期天气良好，无特殊预警"
        })
    
    return {
        "status": "success",
        "city": weather_result["city"],
        "timestamp": weather_result["timestamp"],
        "alerts": alerts,
        "summary": f"共{len(alerts)}条预警信息"
    }


def main():
    cmds = {"now": "查看天气", "outfit": "穿衣建议", "alert": "天气预警"}
    
    if len(sys.argv) < 2 or sys.argv[1] not in cmds:
        print(json.dumps({
            "error": f"用法: weather_advisor_tool.py <{'|'.join(cmds.keys())}> [参数]",
            "available_commands": cmds,
            "example": "python weather_advisor_tool.py now --city Beijing"
        }, ensure_ascii=False, indent=2))
        sys.exit(1)
    
    cmd = sys.argv[1]
    args = sys.argv[2:]
    
    try:
        result = globals()[cmd](args)
        print(json.dumps(result, ensure_ascii=False, indent=2, default=str))
    except Exception as e:
        print(json.dumps({
            "status": "error",
            "message": f"执行出错: {str(e)}"
        }, ensure_ascii=False, indent=2))
        sys.exit(1)


if __name__ == "__main__":
    main()
