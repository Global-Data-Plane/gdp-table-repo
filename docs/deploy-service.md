# Registering the GDP Service as an External JupyterHub Service (Cloud/K8s)

## 1. Generate and Store the API Token

* Generate a strong random API token (hex or UUID):

  ```bash
  openssl rand -hex 32
  # Example output: 6a1b2c3d4e5f67890123456789abcdef0123456789abcdef6a1b2c3d4e5f6789
  ```

* Create a Kubernetes Secret for the token:

  ```yaml
  apiVersion: v1
  kind: Secret
  metadata:
    name: gdp-service-secret
    namespace: <your-jupyterhub-namespace>
  type: Opaque
  stringData:
    gdp_api_token: "<your-token-here>"
  ```

  ```bash
  kubectl apply -f gdp-service-secret.yaml
  ```

## 2. Update Your `values.yaml` for JupyterHub

Add the following under `hub:` in your Helm `values.yaml`:

```yaml
hub:
  services:
    gdp:
      url: "http://gdp-service.gdp-test.svc.cluster.local:5000"
      apiToken:
        valueFrom:
          secretKeyRef:
            name: gdp-service-secret
            key: gdp_api_token
```

* The `url` should match your internal GDP service DNS and port (adjust for your actual names).
* `apiToken` is securely injected from the secret you just created.

## 3. Update Your GDP Deployment to Use the Token

In your GDP deployment YAML, add this to the container `env:`:

```yaml
env:
  - name: JUPYTERHUB_API_TOKEN
    valueFrom:
      secretKeyRef:
        name: gdp-service-secret
        key: gdp_api_token
```

This ensures both JupyterHub and GDP use the same API token for trusted internal calls.

## 4. Apply Your Changes

* Upgrade your Helm release (replace with your release and namespace):

  ```bash
  helm upgrade --namespace <your-jupyterhub-namespace> <release-name> jupyterhub/jupyterhub -f values.yaml
  ```
* Redeploy or restart your GDP service (so it picks up the new env var if needed).

## 5. Confirm and Test

* Check your Hub logs for messages about registering the `gdp` service.
* Test REST API calls via the JupyterHub proxy:

  ```bash
  curl https://<your-hub-domain>/services/gdp/tables -H "Authorization: token <your_user_token>"
  ```
* Try from a notebook in the cloud:

  ```python
  import requests
  token = "<cloud_user_token>"
  url = "http://hub:8081/services/gdp/tables"
  headers = {"Authorization": f"token {token}"}
  print(requests.get(url, headers=headers).text)
  ```

## Common Pitfalls

* The API token in the Hub config and GDP deployment must match **exactly**.
* Service `url` must be the internal cluster DNS/port, not a public IP.
* After updating a secret, restart any pod that consumes it.
* Always check logs for startup or registration errors.

---

*For more: see [JupyterHub external services docs](https://jupyterhub.readthedocs.io/en/stable/reference/services.html) and [Zero to JupyterHub Helm chart](https://z2jh.jupyter.org/en/stable/).*

---
