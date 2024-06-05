#!/bin/bash

git checkout dev
git pull -X theirs dev
sudo systemctl daemon-reload
sudo systemctl restart telegram_bot_dev.service
