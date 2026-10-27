# Kubernetes configuration

## Secrets

`secrets.yaml` defines the Secret objects with **empty data**. Nothing in this
directory contains usable credentials, and workloads will fail to start until
the secrets are provisioned. That is intentional: a pod that cannot find its
database password should crash, not silently use `admin` / `nebula`.

Provision the values out-of-band (see the header of `secrets.yaml`):

```bash
kubectl create secret generic nebula-secrets \
  --from-literal=database-url="postgresql+asyncpg://nebula:$(openssl rand -hex 16)@postgres:5432/nebula" \
  --from-literal=redis-url="redis://redis:6379/0" \
  --from-literal=postgres-user="nebula" \
  --from-literal=postgres-password="$(openssl rand -hex 16)" \
  --from-literal=jwt-secret="$(openssl rand -hex 32)" \
  --from-literal=encryption-key="$(openssl rand -base64 32)"
```

For GitOps, prefer the External Secrets Operator, Sealed Secrets, or SOPS:
commit only the encrypted payload or the remote reference, never plaintext.

`secrets.example.yaml` shows the expected keys for local experiments. It is a
template, not a deployable manifest.

## TLS

`deployments/nginx.yaml` mounts `nebula-ssl-certs`. A `kubernetes.io/tls`
Secret requires a real certificate/key pair, so it is not shipped with
placeholders. Let cert-manager issue it, or create it manually:

```bash
kubectl create secret tls nebula-ssl-certs --cert=fullchain.pem --key=privkey.pem
```
