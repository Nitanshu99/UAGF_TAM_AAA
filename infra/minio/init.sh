#!/bin/sh
# One-shot MinIO provisioning, run by the `minio-init` compose service.
#
#   1. the Langfuse event/media bucket and the EvidenceStore bucket (versioned:
#      an artefact a delivered report cited must survive a later write to the
#      same key);
#   2. one service account per bucket, each attached to a policy that reaches
#      only that bucket, so neither the app nor Langfuse holds the root key.
#      A blank access key / secret skips the account and leaves root in use
#      (local dev fallback) — the policies are created either way.
#
# Idempotent: re-running updates secrets and leaves existing state alone.
# Only `sh` and `mc` are used — the minio/mc image ships neither grep nor sed.
set -eu

mc alias set local http://minio:9000 "$MINIO_ROOT_USER" "$MINIO_ROOT_PASSWORD" >/dev/null
mc mb --ignore-existing "local/$LANGFUSE_S3_BUCKET"
mc mb --ignore-existing "local/$MINIO_BUCKET"
mc version enable "local/$MINIO_BUCKET"

write_policy() {  # <file> <bucket> <object actions, JSON list body>
    cat > "$1" <<EOF
{"Version": "2012-10-17", "Statement": [
  {"Effect": "Allow",
   "Action": ["s3:GetBucketLocation", "s3:ListBucket", "s3:ListBucketMultipartUploads", "s3:GetBucketVersioning"],
   "Resource": ["arn:aws:s3:::$2"]},
  {"Effect": "Allow",
   "Action": [$3],
   "Resource": ["arn:aws:s3:::$2/*"]}
]}
EOF
}

ensure_account() {  # <access key> <secret> <policy name> <bucket> <object actions>
    policy="$3"; bucket="$4"
    write_policy "/tmp/$policy.json" "$bucket" "$5"
    mc admin policy create local "$policy" "/tmp/$policy.json" >/dev/null
    if [ -z "$1" ] || [ -z "$2" ]; then
        echo "policy $policy ready; no service account configured — root credentials stay in use"
        return 0
    fi
    mc admin user add local "$1" "$2" >/dev/null
    # Match the PolicyName line, not the whole output: the access key
    # ("aaa-evidence-rw") contains the policy name ("evidence-rw").
    case "$(mc admin user info local "$1")" in
        *"PolicyName: "*"$policy"*) ;;
        *) mc admin policy attach local "$policy" --user "$1" >/dev/null ;;
    esac
    case "$(mc admin user info local "$1")" in
        *"PolicyName: "*"$policy"*) echo "service account $1 -> policy $policy -> bucket $bucket" ;;
        *) echo "ERROR: policy $policy not attached to $1" >&2; exit 1 ;;
    esac
}

# The app reads and writes artefacts; it never deletes (versioning keeps history).
ensure_account "${MINIO_ACCESS_KEY:-}" "${MINIO_SECRET_KEY:-}" evidence-rw "$MINIO_BUCKET" \
    '"s3:GetObject", "s3:GetObjectVersion", "s3:PutObject", "s3:AbortMultipartUpload", "s3:ListMultipartUploadParts"'
# Langfuse also deletes (media / event retention).
ensure_account "${LANGFUSE_S3_ACCESS_KEY:-}" "${LANGFUSE_S3_SECRET_KEY:-}" langfuse-rw "$LANGFUSE_S3_BUCKET" \
    '"s3:GetObject", "s3:PutObject", "s3:DeleteObject", "s3:AbortMultipartUpload", "s3:ListMultipartUploadParts"'
echo "buckets $LANGFUSE_S3_BUCKET and $MINIO_BUCKET ready"
