#!/bin/bash

repo="${1:-home-assistant/home-assistant}"
token=$(curl -s "https://ghcr.io/token?service=ghcr.io&scope=repository:${repo}:pull" \
             -u "${username}:$(cat $HOME/.docker/ghcr_token)" \
        | jq -r '.token')
curl -H "Authorization: Bearer $token" \
     -s "https://ghcr.io/v2/${repo}/tags/list" | jq .



# Or just use regctl
../build/regclient/bin/regctl manifest get ghcr.io/home-assistant/home-assistant
../build/regclient/bin/regctl manifest head ghcr.io/home-assistant/home-assistant

