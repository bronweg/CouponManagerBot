# CouponManagerBot Helm Chart

Minimal Helm chart for deploying CouponManagerBot in Kubernetes.

## Installation

```bash
declare -A ALLOWED_IDS_MAP=( ["USER_1"]=123 ["USER_2"]=456 )
helm install couponmanagerbot ./couponmanagerbot \
  --set telegram.botToken="YOUR_BOT_TOKEN" \
  --set-json telegram.allowedUserIds=$(jq --compact-output --null-input '$ARGS.positional' --args -- "${ALLOWED_IDS_MAP[@]}")
```

## Database initialization

Create empty database:
```bash
declare -A ALLOWED_IDS_MAP=( ["USER_1"]=123 ["USER_2"]=456 )
helm install couponmanagerbot ./couponmanagerbot \
  --set telegram.botToken="YOUR_BOT_TOKEN" \
  --set-json telegram.allowedUserIds=$(jq --compact-output --null-input '$ARGS.positional' --args -- "${ALLOWED_IDS_MAP[@]}") \
  --set database.init.enabled=true
```

## Configuration

| Parameter | Description | Default |
|-----------|-------------|---------|
| `telegram.botToken` | Telegram bot token | `""` |
| `telegram.allowedUserIds` | List of allowed user IDs | `[]` |
| `database.persistence.enabled` | Enable persistent volume | `true` |
| `database.persistence.size` | Volume size | `1Gi` |
| `database.init.enabled` | Enable database initialization | `false` |