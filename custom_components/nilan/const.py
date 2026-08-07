"""Constants for the Nilan integration."""

DOMAIN = "nilan"

BOARD_TYPE_CTS602 = "CTS602"
BOARD_TYPE_CTS700 = "CTS700"
BOARD_TYPE_CTS700_LEGACY = "CTS700_LEGACY"
# CTS400 reserved until a verified Modbus map and dump exist (docs/naering/cts400.md).
BOARD_TYPES = (BOARD_TYPE_CTS602, BOARD_TYPE_CTS700, BOARD_TYPE_CTS700_LEGACY)
