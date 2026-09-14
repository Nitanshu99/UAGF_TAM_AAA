-- Remove the Langfuse v2 tables that were created inside the application
-- database (aaa) before Langfuse got its own database.
--
-- Context: until commit d5c8b37 the Langfuse container pointed at
-- ${POSTGRES_DB}, so its Prisma migrations created 40 tables next to the
-- alembic_version,checkpoint_blobs,checkpoint_migrations,checkpoint_writes,checkpoints,engagements,evidence_artefacts,langgraph_checkpoints tables Alembic and LangGraph own. Langfuse v4 now migrates the
-- separate `langfuse` database, and the old copies are dead weight.
--
-- Generated 2026-09-11 from the live catalogue. At that time the legacy
-- tables held 0 projects, 0 traces, 0 observations and 0 users, i.e. nothing
-- to migrate. NOT executed automatically: run it once, by hand, after
-- confirming the counts below are still zero.
--
--   docker compose exec -T postgres psql -U $POSTGRES_USER -d $POSTGRES_DB \
--       -f - < infra/postgres/drop-legacy-langfuse-v2.sql

\set ON_ERROR_STOP on

SELECT 'projects' AS legacy_table, count(*) FROM projects
UNION ALL SELECT 'traces', count(*) FROM traces
UNION ALL SELECT 'observations', count(*) FROM observations
UNION ALL SELECT 'users', count(*) FROM users;

BEGIN;

DROP TABLE IF EXISTS
  "Account", "Session", _prisma_migrations, annotation_queue_items, annotation_queues, api_keys, audit_logs, background_migrations, batch_exports, comments, cron_jobs, dataset_items, dataset_run_items, dataset_runs, datasets, eval_templates, events, job_configurations, job_executions, llm_api_keys, media, membership_invitations, models, observation_media, observations, organization_memberships, organizations, posthog_integrations, prices, project_memberships, projects, prompts, score_configs, scores, sso_configs, trace_media, trace_sessions, traces, users, verification_tokens
CASCADE;

-- Prisma enum types that only those tables used.
DROP TYPE IF EXISTS "AnnotationQueueObjectType", "AnnotationQueueStatus", "CommentObjectType", "DatasetStatus", "JobConfigState", "JobExecutionStatus", "JobType", "ObservationLevel", "ObservationType", "Role", "ScoreDataType", "ScoreSource" CASCADE;

COMMIT;
