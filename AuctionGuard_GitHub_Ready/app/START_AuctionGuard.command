#!/bin/bash
cd "$(dirname "$0")"
python3 app.py
STATUS=$?
echo "AuctionGuard stopped (status $STATUS). Press Enter to close."
read -r
