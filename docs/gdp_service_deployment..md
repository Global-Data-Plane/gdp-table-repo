# GDP Service: Settings & Environment Variables

## Environment Variables

| Variable                         | Required    | Description                                                                 | Example / Notes                           |
| -------------------------------- | ----------- | --------------------------------------------------------------------------- | ----------------------------------------- |
| `JUPYTERHUB_API_TOKEN`           | Yes         | Token for authenticating with JupyterHub and/or proxy requests              | Must match token registered in Hub config |
| `GDP_SERVICE_PORT`               | No          | Port the GDP service listens on (default is 5000)                           | `5000`                                    |
| `GDP_SERVICE_HOST`               | No          | Host/IP to bind the service (default is `0.0.0.0`)                          | `0.0.0.0` or `localhost`                  |
| `GOOGLE_PROJECT`                 | No          | (If using Google Cloud integration) Google project ID                       |                                           |
| `GOOGLE_APPLICATION_CREDENTIALS` | No          | Path to Google service account JSON credentials (GCS, BigQuery, etc)        | `/var/secrets/google/key.json`            |
| `BUCKET_NAME`                    | No          | Default GCS bucket for GDP service data storage                             |                                           |
| `GDP_BASE_URL`                   | No          | (Advanced) Public base URL for the service (for callback construction, etc) |                                           |
| `FLASK_SECRET_KEY`               | Recommended | Secret key for Flask session security                                       | Should be strong and random               |

## JupyterHub External Service Registration

* **Service URL:**  Must be the internal K8s DNS for GDP, e.g.
  `http://gdp-service.gdp-test.svc.cluster.local:5000`
* **API Token:**  Injected as `JUPYTERHUB_API_TOKEN` in both GDP and Hub config
* **Secret Storage:**  Use Kubernetes Secrets to manage all tokens, credentials, and keys

## Settings File Example (.env)

```env
# Required for Hub <-> GDP integration
JUPYTERHUB_API_TOKEN=your-very-secret-token

# GDP service host/port
GDP_SERVICE_HOST=0.0.0.0
GDP_SERVICE_PORT=5000

# Optional: GCP integration
GOOGLE_PROJECT=my-gcp-project
GOOGLE_APPLICATION_CREDENTIALS=/var/secrets/google/key.json
BUCKET_NAME=my-gdp-bucket

# Flask secret (session security)
FLASK_SECRET_KEY=some-very-random-string
```

## Cloud Deployment Notes

* **All secrets and sensitive config** should be injected via K8s Secrets, not stored in Docker images or git.
* Always restart pods after updating secrets.
* Double-check that ports in `Service` YAML and `GDP_SERVICE_PORT` match!

## Kubernetes Example

```yaml
env:
  - name: JUPYTERHUB_API_TOKEN
    valueFrom:
      secretKeyRef:
        name: gdp-service-secret
        key: gdp_api_token
  - name: GDP_SERVICE_PORT
    value: "5000"
  - name: GOOGLE_PROJECT
    value: "ultisim"
  # ...other env vars
```

## Troubleshooting

* **400/403 errors:** Usually mean missing or mismatched `JUPYTERHUB_API_TOKEN` between GDP and Hub.
* **502/timeout:** GDP service not running or Service misconfigured.
* **404:** Proxy is forwarding to the wrong route (GDP must expose `/tables`, not `/services/gdp/tables`, when behind the Hub proxy).
