# Deploying coauthored-browse on Google Cloud

coauthored-browse runs on Cloud Run from this repository's `Dockerfile`, reading the
Cloud SQL (MySQL 8) database and the Cloud Storage bucket that
[coauthored-submit](https://github.com/coauthoredai/coauthored-submit) writes (see
`docs/CONTRACT.md`). arXiv's own build and deploy pipelines, which target arXiv's projects,
are not part of this fork.

## One-time setup (shared with coauthored-submit)

```sh
PROJECT=coauthored-prod REGION=us-central1
gcloud projects create $PROJECT && gcloud config set project $PROJECT   # then link billing
gcloud services enable run.googleapis.com sqladmin.googleapis.com artifactregistry.googleapis.com \
  secretmanager.googleapis.com cloudscheduler.googleapis.com
gcloud artifacts repositories create coauthored --repository-format=docker --location=$REGION
gcloud sql instances create coauthored-db --database-version=MYSQL_8_0 --tier=db-f1-micro --region=$REGION
gcloud sql databases create coauthored --instance=coauthored-db
gcloud sql users create browse --instance=coauthored-db --password=...   # read-only grants
gcloud storage buckets create gs://coauthored-papers --location=$REGION --uniform-bucket-level-access
gcloud iam service-accounts create coauthored-browse
gcloud storage buckets add-iam-policy-binding gs://coauthored-papers \
  --member=serviceAccount:coauthored-browse@$PROJECT.iam.gserviceaccount.com --role=roles/storage.objectViewer
printf 'mysql+pymysql://browse:...@/coauthored?unix_socket=/cloudsql/%s:%s:coauthored-db' $PROJECT $REGION \
  | gcloud secrets create browse-db-uri --data-file=-
```

The schema and seed rows are created by coauthored-submit (`flask init-db`).

## Build and deploy

```sh
IMAGE=$REGION-docker.pkg.dev/$PROJECT/coauthored/browse:$(git rev-parse --short HEAD)
gcloud builds submit --tag $IMAGE --build-arg git_commit=$(git rev-parse HEAD) .
gcloud run deploy coauthored-browse --image=$IMAGE --region=$REGION --allow-unauthenticated \
  --service-account=coauthored-browse@$PROJECT.iam.gserviceaccount.com \
  --add-cloudsql-instances=$PROJECT:$REGION:coauthored-db \
  --env-vars-file=deploy/env.yaml --set-secrets=CLASSIC_DB_URI=browse-db-uri:latest
```

`deploy/env.yaml` (copy `env.example.yaml`) sets the public host and storage. Map the domain
with `gcloud run domain-mappings create --service=coauthored-browse --domain=<host>` (or a
load balancer), and route `/submit`, `/account`, `/sign-in`, `/sign-up`, `/sign-out` and
`/moderation` to the coauthored-submit service on the same host.
