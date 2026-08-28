# nhpay

## Icon156_03 모션 미리보기

Figma 키프레임을 2초 루프로 재현하고, 같은 모션을 Lottie JSON으로 구워 둡니다.

```bash
python3 -m http.server 4173 --directory preview
```

Then open http://localhost:4173

- `preview/assets/figma-motion.json`: 전달하신 Figma 모션 키프레임
- `preview/assets/Icon156_03.json`: 같은 타이밍으로 만든 Lottie JSON
- `preview/icon-motion.js`: HOLD / ease-out / spring 플레이어
