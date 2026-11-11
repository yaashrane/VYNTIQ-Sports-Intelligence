# Free-Tier Deployment: Render, Vercel, and PostgreSQL

This deployment uses Render for the FastAPI backend, Vercel for the Vite frontend, and a hosted PostgreSQL database such as Neon. MongoDB is not compatible with the current SQLAlchemy persistence layer.

## 1. Create a PostgreSQL database

Create a PostgreSQL project with your preferred provider and copy its connection URL. For a Neon connection URL, keep its `sslmode=require` option; the backend converts it for the async PostgreSQL driver.

Treat the connection URL as a password. Do not commit it to the repository.

## 2. Deploy the backend to Render

1. In Render, choose **New → Blueprint** and connect this GitHub repository.
2. Select the repository root `render.yaml` and create the service.
3. When prompted, set:
   - `DATABASE_URL` to the PostgreSQL connection URL.
   - `CORS_ORIGINS` temporarily to `http://localhost:3000`; replace it after the Vercel deployment in step 4.
4. Wait for the service to become healthy. Verify `https://<render-service>.onrender.com/api/v1/health`.

The backend creates missing database tables at startup. This bootstraps a new database; it does not migrate changed columns in an existing schema.

## 3. Deploy the frontend to Vercel

1. In Vercel, import the same GitHub repository.
2. Set **Root Directory** to `frontend`.
3. Use the `npm` install command `npm ci`, build command `npm run build`, and output directory `dist`.
4. Add this environment variable for Production (and Preview if needed):

   ```text
   VITE_API_BASE_URL=https://<render-service>.onrender.com/api/v1
   ```

5. Deploy and copy the Vercel production URL.

## 4. Allow the frontend in the backend CORS setting

In the Render service's environment settings, set `CORS_ORIGINS` to the exact Vercel origin, without a trailing slash. For example:

```text
https://<your-project>.vercel.app
```

For local development as well, use a comma-separated value:

```text
https://<your-project>.vercel.app,http://localhost:3000
```

Save the change and let Render redeploy. Use your stable production Vercel domain here, not a short-lived preview URL.

## Free-tier limitations

- Free Render web services can sleep when idle, so the first API request after inactivity may be slow.
- Render's local filesystem is temporary. Uploaded datasets and generated PDF files under `/tmp` can be lost when the service restarts or redeploys. The PostgreSQL database persists separately, but it does not store those files.
- Free database plans have provider-specific quotas and retention limits. Review the provider's current terms and keep backups of important data.
- `create_all` only creates missing tables. Add and run versioned migrations before making schema changes to a database that contains data.
