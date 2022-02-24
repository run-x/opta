Exlude the `kube-system` namespace from the Linkerd proxy injector, like so:

```
kubectl label namespace kube-system config.linkerd.io/admission-webhooks=disabled
```

