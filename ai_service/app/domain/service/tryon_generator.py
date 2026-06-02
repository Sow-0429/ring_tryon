from __future__ import annotations

import io
import urllib.request
from typing import Protocol

from app.domain.service.tryon_compositor import (
    RingAppearance,
    RingPlacement,
    TryOnCompositor,
)

MODE_COMPOSITE = "composite"
MODE_PHOTOREAL = "photoreal"


class GeneratorUnavailableError(Exception):
    """要求された生成モードが利用不可(例: 拡散サービス未設定)。"""


class TryOnGenerator(Protocol):
    """試着画像生成の戦略インターフェース。"""

    def generate(
        self, image_bytes: bytes, placement: RingPlacement, appearance: RingAppearance,
    ) -> bytes: ...


class CompositeGenerator:
    """決定的な合成(Pillow)。全環境で動く既定モード。"""

    def __init__(self) -> None:
        self._compositor = TryOnCompositor()

    def generate(
        self, image_bytes: bytes, placement: RingPlacement, appearance: RingAppearance,
    ) -> bytes:
        return self._compositor.compose(image_bytes, placement, appearance)


class DiffusionGenerator:
    """フォトリアル生成。外部の拡散サービス(DIFFUSION_API_URL)に委譲する。

    モデル本体は同梱しない。URL 未設定なら GeneratorUnavailableError。
    """

    def __init__(self, api_url: str, timeout_sec: float = 120.0) -> None:
        self._api_url = api_url
        self._timeout = timeout_sec

    def generate(
        self, image_bytes: bytes, placement: RingPlacement, appearance: RingAppearance,
    ) -> bytes:
        if not self._api_url:
            raise GeneratorUnavailableError(
                "photoreal generation requires an external diffusion service "
                "(set DIFFUSION_API_URL)"
            )
        # 外部拡散サービスへ画像+プロンプト相当のパラメータを送る(契約は実装側に委ねる)。
        boundary = "----kiraku-diffusion"
        body = _multipart(boundary, image_bytes, placement, appearance)
        req = urllib.request.Request(
            self._api_url,
            data=body,
            headers={"Content-Type": f"multipart/form-data; boundary={boundary}"},
            method="POST",
        )
        with urllib.request.urlopen(req, timeout=self._timeout) as resp:  # noqa: S310
            return resp.read()


def _multipart(
    boundary: str, image: bytes, p: RingPlacement, a: RingAppearance,
) -> bytes:
    buf = io.BytesIO()

    def field(name: str, value: str) -> None:
        buf.write(f"--{boundary}\r\n".encode())
        buf.write(f'Content-Disposition: form-data; name="{name}"\r\n\r\n'.encode())
        buf.write(f"{value}\r\n".encode())

    buf.write(f"--{boundary}\r\n".encode())
    buf.write(b'Content-Disposition: form-data; name="image"; filename="hand.jpg"\r\n')
    buf.write(b"Content-Type: image/jpeg\r\n\r\n")
    buf.write(image)
    buf.write(b"\r\n")
    field("center_x", str(p.center_x))
    field("center_y", str(p.center_y))
    field("width_ratio", str(p.width_ratio))
    field("angle_deg", str(p.angle_deg))
    field("metal", a.metal)
    field("gem", a.gem)
    buf.write(f"--{boundary}--\r\n".encode())
    return buf.getvalue()


def generator_for_mode(mode: str, diffusion_api_url: str = "") -> TryOnGenerator:
    """モードに応じた生成戦略を返す。"""
    if mode == MODE_PHOTOREAL:
        return DiffusionGenerator(diffusion_api_url)
    return CompositeGenerator()
