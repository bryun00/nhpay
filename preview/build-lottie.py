#!/usr/bin/env python3
"""Bake Icon156_03 Figma motion into a playable Lottie JSON."""

from __future__ import annotations

import json
import math
from pathlib import Path

FPS = 60
DURATION_MS = 2000
FRAMES = round(DURATION_MS / 1000 * FPS)


def ms_to_frame(ms: float) -> float:
    return ms / 1000 * FPS


def cubic_bezier_y(x: float, p1x: float, p1y: float, p2x: float, p2y: float) -> float:
    if x <= 0:
        return 0
    if x >= 1:
        return 1
    t = x
    for _ in range(8):
        mt = 1 - t
        bx = 3 * mt * mt * t * p1x + 3 * mt * t * t * p2x + t * t * t
        dx = 3 * mt * mt * p1x + 6 * mt * t * (p2x - p1x) + 3 * t * t * (1 - p2x)
        if abs(dx) < 1e-6:
            break
        t = min(1, max(0, t - (bx - x) / dx))
    mt = 1 - t
    return 3 * mt * mt * t * p1y + 3 * mt * t * t * p2y + t * t * t


def spring_value(local_t: float, duration_ms: float, start: float, end: float) -> float:
    mass, stiffness, damping = 1.0, 600.0, 15.0
    wn = math.sqrt(stiffness / mass)
    zeta = damping / (2 * math.sqrt(stiffness * mass))
    t = local_t * duration_ms / 1000
    delta = end - start
    wd = wn * math.sqrt(1 - zeta * zeta)
    envelope = math.exp(-zeta * wn * t)
    return end - envelope * (delta * math.cos(wd * t) + (zeta * wn * delta / wd) * math.sin(wd * t))


def sample(keyframes: list[dict], time_ms: float) -> float:
    if time_ms <= keyframes[0]["timeMs"]:
        return keyframes[0]["value"]
    if time_ms >= keyframes[-1]["timeMs"]:
        return keyframes[-1]["value"]
    for i, frm in enumerate(keyframes[:-1]):
        to = keyframes[i + 1]
        if time_ms > to["timeMs"]:
            continue
        duration = to["timeMs"] - frm["timeMs"]
        if duration <= 0:
            return to["value"]
        local_t = (time_ms - frm["timeMs"]) / duration
        easing = frm.get("easingToNext") or {}
        if easing.get("hold"):
            return frm["value"]
        if easing.get("springValues"):
            return spring_value(local_t, duration, frm["value"], to["value"])
        if easing.get("bezierValues"):
            b = easing["bezierValues"]
            p = cubic_bezier_y(local_t, b["p1x"], b["p1y"], b["p2x"], b["p2y"])
            return frm["value"] + (to["value"] - frm["value"]) * p
        return frm["value"] + (to["value"] - frm["value"]) * local_t
    return keyframes[-1]["value"]


def hold_kf(t: float, value: list[float], hold: bool = False) -> dict:
    kf: dict = {"t": t, "s": value}
    if hold:
        kf["h"] = 1
    else:
        kf["i"] = {"x": [0.58], "y": [1]}
        kf["o"] = {"x": [0], "y": [0]}
    return kf


def baked_keyframes(times_values: list[tuple[float, list[float]]]) -> dict:
    keys = []
    for i, (t, value) in enumerate(times_values):
        item = {"t": t, "s": value}
        if i < len(times_values) - 1:
            item["i"] = {"x": [0.58], "y": [1]}
            item["o"] = {"x": [0], "y": [0]}
        keys.append(item)
    return {"a": 1, "k": keys}


def rect_shape(w: float, h: float, r: float, color: list[float]) -> list[dict]:
    return [
        {
            "ty": "rc",
            "d": 1,
            "s": {"a": 0, "k": [w, h]},
            "p": {"a": 0, "k": [w / 2, h / 2]},
            "r": {"a": 0, "k": r},
        },
        {"ty": "fl", "c": {"a": 0, "k": color}, "o": {"a": 0, "k": 100}, "r": 1},
        {"ty": "tr", "p": {"a": 0, "k": [0, 0]}, "a": {"a": 0, "k": [0, 0]}, "s": {"a": 0, "k": [100, 100]}, "r": {"a": 0, "k": 0}, "o": {"a": 0, "k": 100}, "sk": {"a": 0, "k": 0}, "sa": {"a": 0, "k": 0}},
    ]


def ellipse_shape(size: float, color: list[float]) -> list[dict]:
    check = [
        [size * 5 / 22, size * 11.2 / 22],
        [size * 9.1 / 22, size * 15.4 / 22],
        [size * 17 / 22, size * 6.8 / 22],
    ]
    zeros = [[0, 0] for _ in check]
    identity = {
        "ty": "tr",
        "p": {"a": 0, "k": [0, 0]},
        "a": {"a": 0, "k": [0, 0]},
        "s": {"a": 0, "k": [100, 100]},
        "r": {"a": 0, "k": 0},
        "o": {"a": 0, "k": 100},
        "sk": {"a": 0, "k": 0},
        "sa": {"a": 0, "k": 0},
    }
    return [
        {
            "ty": "gr",
            "nm": "circle",
            "it": [
                {
                    "ty": "el",
                    "d": 1,
                    "s": {"a": 0, "k": [size, size]},
                    "p": {"a": 0, "k": [size / 2, size / 2]},
                },
                {"ty": "fl", "c": {"a": 0, "k": color}, "o": {"a": 0, "k": 100}, "r": 1},
                identity,
            ],
        },
        {
            "ty": "gr",
            "nm": "check",
            "it": [
                {
                    "ty": "sh",
                    "d": 1,
                    "ks": {"a": 0, "k": {"c": False, "v": check, "i": zeros, "o": zeros}},
                },
                {
                    "ty": "st",
                    "c": {"a": 0, "k": [1, 1, 1, 1]},
                    "o": {"a": 0, "k": 100},
                    "w": {"a": 0, "k": 2.4 * size / 22},
                    "lc": 2,
                    "lj": 2,
                },
                identity,
            ],
        },
    ]


def layer(name: str, ind: int, shapes: list, pos: dict, opacity: dict, scale: dict, anchor: list[float]) -> dict:
    return {
        "ddd": 0,
        "ind": ind,
        "ty": 4,
        "nm": name,
        "sr": 1,
        "ks": {
            "o": opacity,
            "r": {"a": 0, "k": 0},
            "p": pos,
            "a": {"a": 0, "k": anchor},
            "s": scale,
        },
        "ao": 0,
        "shapes": shapes if shapes and shapes[0].get("ty") == "gr" and "it" in shapes[0] else [{"ty": "gr", "nm": name, "it": shapes}],
        "ip": 0,
        "op": FRAMES,
        "st": 0,
        "bm": 0,
    }


def sample_track(kfs: list[dict], mapper=lambda v: v) -> dict:
    frames = []
    for f in range(FRAMES + 1):
        ms = f / FPS * 1000
        frames.append((float(f), [mapper(sample(kfs, ms))]))
    # downsample identical holds: keep first, last, and changes
    compact = [frames[0]]
    for prev, cur in zip(frames, frames[1:]):
        if abs(cur[1][0] - prev[1][0]) > 0.02 or cur[0] == FRAMES:
            compact.append(cur)
    if compact[-1][0] != FRAMES:
        compact.append(frames[-1])
    return baked_keyframes(compact)


def xy_track(x_kfs: list[dict], y_kfs: list[dict]) -> dict:
    frames = []
    for f in range(FRAMES + 1):
        ms = f / FPS * 1000
        frames.append((float(f), [sample(x_kfs, ms), sample(y_kfs, ms)]))
    compact = [frames[0]]
    for prev, cur in zip(frames, frames[1:]):
        if abs(cur[1][0] - prev[1][0]) > 0.02 or abs(cur[1][1] - prev[1][1]) > 0.02 or cur[0] == FRAMES:
            compact.append(cur)
    keys = []
    for i, (t, value) in enumerate(compact):
        item = {"t": t, "s": value}
        if i < len(compact) - 1:
            item["i"] = {"x": [0.58, 0.58], "y": [1, 1]}
            item["o"] = {"x": [0, 0], "y": [0, 0]}
        keys.append(item)
    return {"a": 1, "k": keys}


def main() -> None:
    motion = json.loads(Path("preview/assets/figma-motion.json").read_text())
    nodes = {n["node"]: {f["field"].split("@")[0]: f["keyframes"] for f in n["fields"]} for n in motion["nodes"]}

    n1143, n1144, n1145, n1151 = nodes["54:1143"], nodes["54:1144"], nodes["54:1145"], nodes["54:1151"]

    card_w, card_h, card_r = 102, 66, 14
    badge = 44

    layers = [
        layer(
            "54:1145",
            1,
            rect_shape(card_w, card_h, card_r, [0.435, 0.749, 0.561, 1]),
            xy_track(n1145["motionTranslationX"], n1145["motionTranslationY"]),
            sample_track(n1145["opacity"]),
            {"a": 0, "k": [100, 100, 100]},
            [0, 0],
        ),
        layer(
            "54:1144",
            2,
            rect_shape(card_w, card_h, card_r, [0.718, 0.878, 0.784, 1]),
            xy_track(n1144["motionTranslationX"], n1144["motionTranslationY"]),
            sample_track(n1144["opacity"]),
            {"a": 0, "k": [100, 100, 100]},
            [0, 0],
        ),
        layer(
            "54:1143",
            3,
            rect_shape(card_w, card_h, card_r, [1, 1, 1, 1]),
            xy_track(n1143["motionTranslationX"], n1143["motionTranslationY"]),
            sample_track(n1143["opacity"]),
            {"a": 0, "k": [100, 100, 100]},
            [0, 0],
        ),
        layer(
            "54:1151",
            4,
            ellipse_shape(badge, [0, 0.651, 0.318, 1]),
            {"a": 0, "k": [86 + badge / 2, 78 + badge / 2]},
            sample_track(n1151["opacity"]),
            {
                "a": 1,
                "k": [
                    {"t": t, "s": [sx, sy, 100]}
                    for t, (sx, sy) in (
                        (
                            float(f),
                            (
                                sample(n1151["motionScaleX"], f / FPS * 1000) * 100,
                                sample(n1151["motionScaleY"], f / FPS * 1000) * 100,
                            ),
                        )
                        for f in range(FRAMES + 1)
                        if f == 0
                        or f == FRAMES
                        or abs(sample(n1151["motionScaleX"], f / FPS * 1000) - sample(n1151["motionScaleX"], (f - 1) / FPS * 1000)) > 0.004
                    )
                ],
            },
            [badge / 2, badge / 2],
        ),
    ]

    # fix scale keyframes easing
    scale_k = layers[-1]["ks"]["s"]["k"]
    for i, kf in enumerate(scale_k):
        if i < len(scale_k) - 1:
            kf["i"] = {"x": [0.58, 0.58, 0.58], "y": [1, 1, 1]}
            kf["o"] = {"x": [0, 0, 0], "y": [0, 0, 0]}

    data = {
        "v": "5.7.0",
        "fr": FPS,
        "ip": 0,
        "op": FRAMES,
        "w": 156,
        "h": 156,
        "nm": "Icon156_03",
        "ddd": 0,
        "assets": [],
        "layers": list(reversed(layers)),
        "meta": {"g": "Icon156_03 Figma motion rebuild"},
    }
    out = Path("preview/assets/Icon156_03.json")
    out.write_text(json.dumps(data, separators=(",", ":")))
    print(f"wrote {out} ({out.stat().st_size} bytes), layers={len(data['layers'])}")


if __name__ == "__main__":
    main()
