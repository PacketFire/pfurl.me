kubectl --server="$GKE_APISERVER" \
        --namespace="$GKE_NAMESPACE" \
        --token="$GKE_BEARER_TOKEN" \
        --insecure-skip-tls-verify=true \
        set image packetfire/pfurl pfurl=gcr.io/$GCP_PROJECT_ID/pfurl.me:$TRAVIS_COMMIT