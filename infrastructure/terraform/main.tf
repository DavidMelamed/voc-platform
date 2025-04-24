# Terraform configuration for Astra DB and Astra Streaming resources

terraform {
  required_providers {
    astra = {
      source  = "datastax/astra"
      version = "~> 2.1.0"
    }
  }
}

provider "astra" {
  token = var.astra_token
}

# Create Astra DB database
resource "astra_database" "voc_platform" {
  name           = "${var.tenant_name}-voc-platform"
  cloud_provider = var.cloud_provider
  region         = var.region
  keyspace       = var.keyspace
  tier           = var.db_tier
}

# Create Astra Streaming tenant
resource "astra_streaming_tenant" "voc_platform" {
  tenant_name = "${var.tenant_id}-voc-platform"
  region      = var.region
  cloud       = var.cloud_provider
}

# Create namespace for tenant's streaming resources
resource "astra_streaming_namespace" "voc_platform" {
  tenant_name = astra_streaming_tenant.voc_platform.tenant_name
  namespace   = "${var.tenant_id}-ns"
  region      = var.region
}

# Create Pulsar topics for the platform
resource "astra_streaming_topic" "scrape_jobs" {
  tenant_name = astra_streaming_tenant.voc_platform.tenant_name
  namespace   = astra_streaming_namespace.voc_platform.namespace
  topic       = "scrape.jobs"
  region      = var.region
  partitions  = 3
  retention_policies {
    retention_size_in_mb   = 512
    retention_time_in_mins = 10080 # 7 days
  }
}

resource "astra_streaming_topic" "scrape_results" {
  tenant_name = astra_streaming_tenant.voc_platform.tenant_name
  namespace   = astra_streaming_namespace.voc_platform.namespace
  topic       = "scrape.results"
  region      = var.region
  partitions  = 3
  retention_policies {
    retention_size_in_mb   = 1024
    retention_time_in_mins = 10080 # 7 days
  }
}

resource "astra_streaming_topic" "tag_complete" {
  tenant_name = astra_streaming_tenant.voc_platform.tenant_name
  namespace   = astra_streaming_namespace.voc_platform.namespace
  topic       = "tag.complete"
  region      = var.region
  partitions  = 3
  retention_policies {
    retention_size_in_mb   = 512
    retention_time_in_mins = 10080 # 7 days
  }
}

resource "astra_streaming_topic" "analysis_jobs" {
  tenant_name = astra_streaming_tenant.voc_platform.tenant_name
  namespace   = astra_streaming_namespace.voc_platform.namespace
  topic       = "analysis.jobs"
  region      = var.region
  partitions  = 2
  retention_policies {
    retention_size_in_mb   = 256
    retention_time_in_mins = 10080 # 7 days
  }
}

resource "astra_streaming_topic" "analysis_done" {
  tenant_name = astra_streaming_tenant.voc_platform.tenant_name
  namespace   = astra_streaming_namespace.voc_platform.namespace
  topic       = "analysis.done"
  region      = var.region
  partitions  = 2
  retention_policies {
    retention_size_in_mb   = 256
    retention_time_in_mins = 10080 # 7 days
  }
}

# Initialize keyspace schema
resource "null_resource" "init_schema" {
  depends_on = [astra_database.voc_platform]

  provisioner "local-exec" {
    command = <<EOT
      curl -s -L -X POST ${astra_database.voc_platform.graphql_url}/admin \
        -H 'X-Cassandra-Token: ${var.astra_token}' \
        -H 'Content-Type: application/json' \
        -d '{
          "query": "
            # Create raw_docs table
            CREATE TABLE IF NOT EXISTS ${var.keyspace}.raw_docs (
              tenant_id text,
              doc_id uuid,
              source_type text,
              content text,
              metadata map<text, text>,
              created_at timestamp,
              updated_at timestamp,
              PRIMARY KEY ((tenant_id), doc_id)
            );
            
            # Create vectors table with vector search index
            CREATE TABLE IF NOT EXISTS ${var.keyspace}.vectors (
              tenant_id text,
              doc_id uuid,
              chunk_id uuid,
              embedding vector<float, 1536>,
              text text,
              metadata map<text, text>,
              PRIMARY KEY ((tenant_id), doc_id, chunk_id)
            );
            
            # Create graph_edges table
            CREATE TABLE IF NOT EXISTS ${var.keyspace}.graph_edges (
              tenant_id text,
              from_id uuid,
              relation_type text,
              to_id uuid,
              weight float,
              properties map<text, text>,
              PRIMARY KEY ((tenant_id, from_id), relation_type, to_id)
            );
            
            # Create insights table
            CREATE TABLE IF NOT EXISTS ${var.keyspace}.insights (
              tenant_id text,
              insight_id uuid,
              title text,
              description text,
              source_ids list<uuid>,
              created_at timestamp,
              artifact_urls list<text>,
              metadata map<text, text>,
              PRIMARY KEY ((tenant_id), insight_id)
            );
            
            # Create vector search index
            CREATE CUSTOM INDEX IF NOT EXISTS vectors_embedding_idx 
            ON ${var.keyspace}.vectors (embedding) 
            USING 'StorageAttachedIndex'
            WITH OPTIONS = {
              'similarity_function': 'cosine'
            };
          "
        }'
    EOT
  }
}
