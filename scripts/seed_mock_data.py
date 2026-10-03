from __future__ import annotations

from app.integrations.mock.generator import build_overview_payload


def main() -> None:
    payload = build_overview_payload()
    print("Mock data generated for overview report:")
    print(payload)


if __name__ == "__main__":
    main()
