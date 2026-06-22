CREATE EXTENSION IF NOT EXISTS pgcrypto;

CREATE TABLE IF NOT EXISTS sources (
  id UUID PRIMARY KEY DEFAULT gen_random_uuid(), name VARCHAR(200) NOT NULL, type VARCHAR(50) NOT NULL,
  url TEXT NOT NULL, query TEXT NOT NULL DEFAULT '', enabled BOOLEAN NOT NULL DEFAULT TRUE,
  collection_prompt TEXT NOT NULL DEFAULT '', refresh_interval INTEGER NOT NULL DEFAULT 360,
  last_checked_at TIMESTAMPTZ, created_at TIMESTAMPTZ NOT NULL DEFAULT now(), updated_at TIMESTAMPTZ NOT NULL DEFAULT now()
);
CREATE TABLE IF NOT EXISTS projects (
  id UUID PRIMARY KEY DEFAULT gen_random_uuid(), url TEXT UNIQUE NOT NULL, title VARCHAR(500) NOT NULL,
  description TEXT NOT NULL DEFAULT '', summary TEXT NOT NULL DEFAULT '', source_type VARCHAR(50) NOT NULL DEFAULT 'webpage',
  project_type VARCHAR(50) NOT NULL DEFAULT 'Application', subtype VARCHAR(100) NOT NULL DEFAULT 'Other',
  difficulty VARCHAR(20) NOT NULL DEFAULT 'Intermediate', hardware_requirements JSONB NOT NULL DEFAULT '[]',
  software_requirements JSONB NOT NULL DEFAULT '[]', inspired_ideas JSONB NOT NULL DEFAULT '[]', idea_value DOUBLE PRECISION NOT NULL DEFAULT 0,
  stars INTEGER NOT NULL DEFAULT 0, views INTEGER NOT NULL DEFAULT 0, likes INTEGER NOT NULL DEFAULT 0,
  external_created_at TIMESTAMPTZ, external_updated_at TIMESTAMPTZ, status VARCHAR(20) NOT NULL DEFAULT 'pending',
  error TEXT, extra JSONB NOT NULL DEFAULT '{}', source_id UUID REFERENCES sources(id) ON DELETE SET NULL,
  created_at TIMESTAMPTZ NOT NULL DEFAULT now(), updated_at TIMESTAMPTZ NOT NULL DEFAULT now()
);
CREATE TABLE IF NOT EXISTS tags (id UUID PRIMARY KEY DEFAULT gen_random_uuid(), name VARCHAR(100) UNIQUE NOT NULL);
CREATE TABLE IF NOT EXISTS project_tags (project_id UUID REFERENCES projects(id) ON DELETE CASCADE, tag_id UUID REFERENCES tags(id) ON DELETE CASCADE, PRIMARY KEY(project_id, tag_id));
CREATE TABLE IF NOT EXISTS metrics_history (id UUID PRIMARY KEY DEFAULT gen_random_uuid(), project_id UUID NOT NULL REFERENCES projects(id) ON DELETE CASCADE, stars INTEGER DEFAULT 0, views INTEGER DEFAULT 0, likes INTEGER DEFAULT 0, recorded_at TIMESTAMPTZ DEFAULT now());
CREATE TABLE IF NOT EXISTS raw_documents (id UUID PRIMARY KEY DEFAULT gen_random_uuid(), project_id UUID NOT NULL REFERENCES projects(id) ON DELETE CASCADE, content TEXT NOT NULL, metadata JSONB DEFAULT '{}', fetched_at TIMESTAMPTZ DEFAULT now());
CREATE TABLE IF NOT EXISTS embeddings (id UUID PRIMARY KEY DEFAULT gen_random_uuid(), project_id UUID NOT NULL REFERENCES projects(id) ON DELETE CASCADE, qdrant_point_id VARCHAR(100) NOT NULL, provider VARCHAR(30) NOT NULL, model VARCHAR(200) NOT NULL, created_at TIMESTAMPTZ DEFAULT now(), UNIQUE(project_id, provider, model));
CREATE TABLE IF NOT EXISTS collection_logs (id UUID PRIMARY KEY DEFAULT gen_random_uuid(), source_id UUID REFERENCES sources(id) ON DELETE SET NULL, status VARCHAR(30) NOT NULL, message TEXT DEFAULT '', projects_found INTEGER DEFAULT 0, projects_added INTEGER DEFAULT 0, started_at TIMESTAMPTZ DEFAULT now(), finished_at TIMESTAMPTZ);
CREATE TABLE IF NOT EXISTS settings (key VARCHAR(100) PRIMARY KEY, value TEXT NOT NULL DEFAULT '', is_secret BOOLEAN NOT NULL DEFAULT FALSE, updated_at TIMESTAMPTZ DEFAULT now());
CREATE INDEX IF NOT EXISTS ix_projects_type ON projects(project_type);
CREATE INDEX IF NOT EXISTS ix_projects_source ON projects(source_type);
CREATE INDEX IF NOT EXISTS ix_projects_status ON projects(status);
CREATE INDEX IF NOT EXISTS ix_sources_type ON sources(type);

