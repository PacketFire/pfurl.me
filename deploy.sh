#!/bin/bash

kubectl --server="$GKE_APISERVER" \
        --namespace="$GKE_NAMESPACE" \
        --token="$GKE_BEARER_TOKEN" \
        --insecure-skip-tls-verify=true \
        set image deployment/pfurl pfurl=gcr.io/$GCP_PROJECT_ID/pfurl:$TRAVIS_COMMIT
