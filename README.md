# nhpay

## Icon156_03 모션 미리보기

`preview/`에서 GIF, MP4, SVG, CSS, Lottie JSON을 같은 156×156 스테이지로 확인합니다.

```bash
python3 -m http.server 4173 --directory preview
```

Then open http://localhost:4173

- **SVG + CSS**: 벡터 아이콘 모션을 Lottie JSON으로 구현하기 가장 좋습니다.
- **GIF / MP4**: 바로 재생해서 보고, 같은 모션을 벡터 JSON으로 다시 그립니다.
- **Lottie JSON**: 레이어가 있으면 그대로 재생합니다.
